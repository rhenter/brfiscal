from django.db import models

from .validators import validar_cest, validar_ncm


class NcmField(models.CharField):
    """CharField de 8 dígitos validado contra a tabela NCM vigente."""

    default_validators = [validar_ncm]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 8)
        kwargs.setdefault("verbose_name", "NCM")
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        value = super().to_python(value)
        return "".join(c for c in value if c.isdigit()) if value else value


class CestField(models.CharField):
    default_validators = [validar_cest]

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("max_length", 7)
        kwargs.setdefault("verbose_name", "CEST")
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        value = super().to_python(value)
        return "".join(c for c in value if c.isdigit()) if value else value
