from neuroscout.utils.db import put_record


def update_record(model, exception=None, **fields):
    if exception is not None:
        if 'traceback' in fields:
            fields['traceback'] = f"{fields['traceback']} \n {str(exception)}"
        if 'status' not in fields:
            fields['status'] = 'FAILED'
    put_record(fields, model)
    return fields
