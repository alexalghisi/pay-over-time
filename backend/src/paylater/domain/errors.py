class DomainError(Exception):
    code = "domain_error"
    status_code = 422


class AmountOutOfRange(DomainError):
    code = "amount_out_of_range"


class UnsupportedTerm(DomainError):
    code = "unsupported_term"


class InvalidPayment(DomainError):
    code = "invalid_payment"


class PlanNotFound(DomainError):
    code = "plan_not_found"
    status_code = 404
