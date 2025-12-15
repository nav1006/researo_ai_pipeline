import json
from typing import Dict
from auth import decode_token
from models import UserRole

def can_access_document(user_token: str, doc: Dict) -> bool:
    payload = decode_token(user_token)
    if not payload:
        return False

    user_role = payload.get("role")
    user_id = payload.get("sub")
    access_level = doc.get("access_level")

    if user_role in [UserRole.ADMIN.value, UserRole.TEACHER.value]:
        return True

    if user_role == UserRole.STUDENT.value:
        if access_level == "public":
            return True
        if access_level == "specific_students":
            allowed_ids_str = doc.get("allowed_student_ids", "[]")
            try:
                allowed_ids = json.loads(allowed_ids_str) if isinstance(allowed_ids_str, str) else allowed_ids_str
            except json.JSONDecodeError:
                allowed_ids = []
            return user_id in allowed_ids
        if access_level == "class_group":
            # Implement class group membership check
            user_classes = []  # Should be fetched from user data
            class_group = doc.get("class_group")
            return class_group in user_classes

    return False
