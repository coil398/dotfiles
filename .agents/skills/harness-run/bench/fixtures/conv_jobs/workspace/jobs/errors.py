class JobError(Exception):
    pass


class TransientError(JobError):
    pass


class StoreUnavailable(TransientError):
    pass
