from solpic_worker_server.utils import (
    get_answer,
    get_answer_number,
    reconstruct_solving,
    upload_to_s3,
)
from solpic_worker_server.external_services.huggingface import request_huggingface_async
from solpic_worker_server.external_services.math_ocr import request_ocr_from_upload_file
from solpic_worker_server.external_services.translation import request_translation
from solpic_worker_server.utils.divide_solving import divide_solving
from solpic_worker_server.utils.analyzeOcrText import analyze_ocr_text

from worker import app
from pymongo import MongoClient
from bson import ObjectId
import base64

mongo = MongoClient("mongodb://mongo:27017")
db = mongo["your_db_name"]
progress_col = db["analyze_progress"]
problem_col = db["problems"]


def update_stage(device_id: str, field: str, status: str):
    progress_col.update_one({"device_id": device_id}, {"$set": {field: status}})


def process_ocr(device_id: str, file_base64: str) -> str:
    try:
        update_stage(device_id, "ocr_stage", "in_progress")
        ocr_text = request_ocr_from_upload_file(file_base64)
        update_stage(device_id, "ocr_stage", "success")

        return ocr_text
    except Exception as error:
        update_stage(device_id, "ocr_stage", "failed")
        raise error


def process_translation_to_en(device_id: str, ocr_text: str) -> str:
    try:
        update_stage(device_id, "translate_to_en_stage", "in_progress")
        lang = analyze_ocr_text(ocr_text)

        if lang == "Kor":
            translated = request_translation([ocr_text], "EN")
            en_text = translated[0]["text"]
        else:
            en_text = ocr_text

        update_stage(device_id, "translate_to_en_stage", "success")

        return en_text
    except Exception as error:
        update_stage(device_id, "translate_to_en_stage", "failed")

        raise error


def process_ai_inference(device_id: str, en_text: str) -> str:
    try:
        update_stage(device_id, "AI_inference_stage", "in_progress")
        ai_explanation = request_huggingface_async(en_text)
        update_stage(device_id, "AI_inference_stage", "success")

        return ai_explanation
    except Exception as error:
        update_stage(device_id, "AI_inference_stage", "failed")

        raise error


def process_translation_to_ko(device_id: str, ai_explanation: str) -> str:
    try:
        update_stage(device_id, "translate_to_ko_stage", "in_progress")

        en_answer, math_answer = divide_solving(ai_explanation)
        translated_back = request_translation(en_answer, "KO")
        ko_texts = [item["text"] for item in translated_back]
        ko_explanation = reconstruct_solving(ko_texts, math_answer)

        update_stage(device_id, "translate_to_ko_stage", "success")

        return ko_explanation
    except Exception as error:
        update_stage(device_id, "translate_to_ko_stage", "failed")

        raise error


def process_upload_and_save(
    device_id: str,
    problem_id: str,
    file_base64: str,
    filename: str,
    en_text: str,
    ai_explanation: str,
    ko_explanation: str,
):
    try:
        update_stage(device_id, "save_and_respond_stage", "in_progress")

        image_bytes = base64.b64decode(file_base64)
        problem_type = "default"
        key = upload_to_s3(image_bytes, "sol.pic", filename, problem_type)
        answer = get_answer_number(en_text, get_answer(ai_explanation))

        problem_col.update_one(
            {"_id": ObjectId(problem_id)},
            {
                "$set": {
                    "key": key,
                    "ko_question_text": "",
                    "en_question_text": en_text,
                    "problem_type": problem_type,
                    "ko_explanation": ko_explanation,
                    "en_explanation": ai_explanation,
                    "answer": answer,
                }
            },
        )

        update_stage(device_id, "save_and_respond_stage", "success")
    except Exception as error:
        update_stage(device_id, "save_and_respond_stage", "failed")

        raise error


@app.task(name="tasks.analyze_pipeline.run_full_analysis")
def run_full_analysis(problem_id: str, device_id: str, file_base64: str, filename: str):
    ocr_text = process_ocr(device_id, file_base64)
    en_text = process_translation_to_en(device_id, ocr_text)
    ai_explanation = process_ai_inference(device_id, en_text)
    ko_explanation = process_translation_to_ko(device_id, ai_explanation)

    process_upload_and_save(
        device_id,
        problem_id,
        file_base64,
        filename,
        en_text,
        ai_explanation,
        ko_explanation,
    )
