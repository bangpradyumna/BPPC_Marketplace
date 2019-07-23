import random
import string

from rest_framework_jwt.settings import api_settings

HOSTELS = {
	"RM" : "Ram Bhawan",
	"BUDH": "Budh Bhawan",
	"SR-A": "Srinivasa Ramanujan A",
	"SR-B": "Srinivasa Ramanujan B",
	"SR-C": "Srinivasa Ramanujan C",
	"SR-D": "Srinivasa Ramanujan D",
	"KR": "Krishna Bhawan",
	"GN": "Gandhi Bhawan",
	"SK": "Shankar Bhawan",
	"VY": "Vyas Bhawan",
	"VK": "Vishwakarma Bhawan",
	"BG": "Bhagirath Bhawan",
	"RP": "Rana Pratap Bhawan",
	"AK": "Ashok Bhawan",
	"MV-A": "Malviya-A Bhawan",
	"MV-B": "Malviya-B Bhawan",
	"MV-C": "Malviya-C Bhawan",
	"MR-1": "Meera Bhawan Block-1",
	"MR-2": "Meera Bhawan Block-2",
	"MR-3": "Meera Bhawan Block-3",
	"MR-4": "Meera Bhawan Block-4",
	"MR-5": "Meera Bhawan Block-5",
	"MR-6": "Meera Bhawan Block-6",
	"MR-7": "Meera Bhawan Block-7",
	"MR-8": "Meera Bhawan Block-8",
	"MR-9": "Meera Bhawan Block-9",
	"MR-10": "Meera Bhawan Block-10",
}

GIRLS_HOSTEL = {
	"MR-1": "Meera Bhawan Block-1",
	"MR-2": "Meera Bhawan Block-2",
	"MR-3": "Meera Bhawan Block-3",
	"MR-4": "Meera Bhawan Block-4",
	"MR-5": "Meera Bhawan Block-5",
	"MR-6": "Meera Bhawan Block-6",
	"MR-7": "Meera Bhawan Block-7",
	"MR-8": "Meera Bhawan Block-8",
	"MR-9": "Meera Bhawan Block-9",
	"MR-10": "Meera Bhawan Block-10",
}

BOYS_HOSTEL = {
	"RM" : "Ram Bhawan",
	"BUDH": "Budh Bhawan",
	"SR-A": "Srinivasa Ramanujan A",
	"SR-B": "Srinivasa Ramanujan B",
	"SR-C": "Srinivasa Ramanujan C",
	"SR-D": "Srinivasa Ramanujan D",
	"KR": "Krishna Bhawan",
	"GN": "Gandhi Bhawan",
	"SK": "Shankar Bhawan",
	"VY": "Vyas Bhawan",
	"VK": "Vishwakarma Bhawan",
	"BG": "Bhagirath Bhawan",
	"RP": "Rana Pratap Bhawan",
	"AK": "Ashok Bhawan",
	"MV-A": "Malviya-A Bhawan",
	"MV-B": "Malviya-B Bhawan",
	"MV-C": "Malviya-C Bhawan"	
}

}

SINGLE_DEGREE_BRANCHES = {
	"A1":"B.E. Chemical",
	"A2":"B.E. Civil",
	"A7":"B.E. Computer Science",
	"A3":"B.E. Electrical & Electronics",
	"A8":"B.E. Electronics & Instrumentation",
	"A4":"B.E. Mechanical",
	"AB":"B.E. Manufacturing",
	"A5":"B.Pharm.",
}

DUAL_DEGREE_BRANCHES = {
	"B1":"M.Sc. Biological Sciences",
	"B2":"M.Sc. Chemistry",
	"B3":"M.Sc. Economics",
	"B4":"M.Sc. Mathematics",
	"B5":"M.Sc. Physics",
}


def generate_random_password():
    PASS_CHARS = string.ascii_letters + string.digits
    for i in '0oO1QlLiI':
        PASS_CHARS = PASS_CHARS.replace(i,'')
    return "".join(random.choice(PASS_CHARS) for _ in range(0, 10))

def get_jwt_with_user(auth_user):
	"""
		Use the GetBlimp djangorestframework-jwt library to generate a JWT.
		For more read: http://getblimp.github.io/django-rest-framework-jwt/
		Source: https://github.com/GetBlimp/django-rest-framework-jwt
	"""
	jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
	jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
	payload = jwt_payload_handler(auth_user)
	token = jwt_encode_handler(payload)
	return token

