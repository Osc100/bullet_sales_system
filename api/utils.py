import functools

from django.utils.translation import gettext_lazy as _
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST


class ResponseBadRequest(Response):
    """Default status code 400 and data values in list, useful to imitate DRF serializer validation errors"""

    status_code: int = HTTP_400_BAD_REQUEST

    def __init__(
        self,
        data=None,
        status=None,
        template_name=None,
        headers=None,
        exception=False,
        content_type=None,
    ):
        """This init method makes data string values into list"""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    data[key] = [value]

        super(ResponseBadRequest, self).__init__(
            data, status, template_name, headers, exception, content_type
        )


def key_error_as_response_bad_request(func):
    @functools.wraps(func)
    def decorator(*args, **kwargs):
        try:
            return_value = func(*args, **kwargs)
        except KeyError as e:
            return ResponseBadRequest({str(e): _("Este campo es requerido")})

        return return_value

    return decorator
