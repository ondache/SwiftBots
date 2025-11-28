class CloseTestAppException(BaseException): ...


def close_test_app():
    raise CloseTestAppException()


def run_raisable(app):
    try:
        app.run()
    except CloseTestAppException:
        ...
