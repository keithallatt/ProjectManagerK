import os.path
from hashlib import sha256
from functools import reduce
import json
from PyInquirer import prompt
from prompt_toolkit.validation import Validator, ValidationError
import re


JSON_FILE = "./.pmk_config.json"

SPECIAL_SYMBOLS = "@#$%^&*()[]{}<>'\",./\\?|`~ +=-_"
VALID_PASSWORD_CHARS = list(map(str, range(10))) + list(map(chr, range(97, 123))) + \
                       list(map(chr, range(65, 91))) + list(SPECIAL_SYMBOLS)


class PasswordValidator(Validator):
    def validate(self, document):
        global __incorrect_attempts, __last_entered_password
        doc_text = document.text

        if not 4 <= len(doc_text) <= 18:
            raise ValidationError(
                message="Please enter a password between 4 and 18 characters",
                cursor_position=len(doc_text)
            )

        if not set(doc_text).issubset(VALID_PASSWORD_CHARS):
            raise ValidationError(
                message=f"Please only use these characters: ([0-9a-zA-Z]|{re.escape(SPECIAL_SYMBOLS)})",
                cursor_position=len(doc_text)
            )

        if __last_entered_password is None:
            __last_entered_password = doc_text
        else:
            if __incorrect_attempts >= 3:
                __last_entered_password = None
                return
            if __last_entered_password != doc_text:
                __incorrect_attempts += 1
                raise ValidationError(
                    message="Please repeat the first password.",
                    cursor_position=len(doc_text)
                )
            __last_entered_password = None


def encode_password(pswd):
    if not (4 <= len(pswd) <= 18):
        print("Password must be between 4 and 18 characters.")
        return None

    base_n = len(VALID_PASSWORD_CHARS)

    if not set(pswd).issubset(set(VALID_PASSWORD_CHARS)):
        print(f"Contained invalid chars: {set(pswd) - set(VALID_PASSWORD_CHARS)}")
        return None

    pswd_indices = list(map(VALID_PASSWORD_CHARS.index, pswd))
    result = reduce(lambda a, b: a * base_n + b, pswd_indices) + 13
    res_squared = result * result
    rs_sq_id = []
    v = res_squared

    while v > 0:
        v, digit = divmod(v, base_n)
        rs_sq_id.append(digit)

    rs_sq_id = rs_sq_id[::2] + rs_sq_id[1::2]
    rs_sq_str = "".join(map(VALID_PASSWORD_CHARS.__getitem__, rs_sq_id))
    h = sha256(rs_sq_str.encode("utf-8"))
    d = list(h.digest())
    d2 = sum(map(lambda x: list(divmod(x, base_n)), d), [])
    d_str = "".join(map(VALID_PASSWORD_CHARS.__getitem__, d2))

    d_result = reduce(lambda a, b: a * 256 + b, d)

    return d_str, d_result


def fudgify_password_result(res, max_size=750):
    def prime_factorization(v, limit=1000):
        factors = []
        d = 2
        while v > 1:
            while v % d == 0:
                factors.append(d)
                v //= d

            d = 3 if d == 2 else 5 if d == 3 else d + 2 if d % 6 == 5 else d + 4
            if d > limit:
                factors.append(v)
                return factors

        return factors

    pf = prime_factorization(res, limit=3*max_size)

    pf = [x if x < max_size else fudgify_password_result(x-1) for x in pf]

    return pf


def fudgify(res):
    fudge = fudgify_password_result(res, max_size=3000)

    def stringify(lst):
        lst = [f"({stringify(l)}+1)" if isinstance(l, list) else l for l in lst]

        return "*".join(map(str, lst))

    str_fudge = stringify(fudge)

    assert eval(str_fudge) == res

    return str_fudge


def check_password(password):
    set_default_password()

    with open(JSON_FILE, 'r') as json_file:
        json_fudge = json.load(json_file)["password:fudge"]
        return encode_password(password)[1] == eval(json_fudge)


def set_password_mainloop():
    questions = [
        {
            'type': 'password',
            'message': '  Enter your new Project Manager password:',
            'name': 'password',
            'validate': PasswordValidator
        },
        {
            'type': 'password',
            'message': '  Repeat the password:',
            'name': 'password_repeat',
            'validate': PasswordValidator
        }

    ]
    res = prompt(questions)

    print(res)

def set_default_password():
    f = fudgify(encode_password("password")[1])

    if not os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'w') as json_file:
            json.dump({"password:fudge": f}, json_file, indent=2)


if __name__ == '__main__':
    set_password_mainloop()
