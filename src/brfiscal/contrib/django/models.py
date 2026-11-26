from django.db import models


class VersaoTabela(models.Model):
    """Qual versão de cada tabela está carregada no banco."""

    tabela = models.CharField(max_length=20, unique=True)
    vigencia = models.DateField()
    ato = models.CharField(max_length=200, blank=True)
    fonte = models.URLField(max_length=500, blank=True)
    total = models.PositiveIntegerField(default=0)
    carregada_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "versão de tabela"
        verbose_name_plural = "versões das tabelas"

    def __str__(self) -> str:
        return f"{self.tabela} ({self.vigencia:%d/%m/%Y})"


class Ncm(models.Model):
    codigo = models.CharField(max_length=8, primary_key=True)
    descricao = models.TextField()
    descricao_completa = models.TextField()
    inicio = models.DateField(null=True, blank=True)
    fim = models.DateField(null=True, blank=True)
    ato = models.CharField(max_length=100, blank=True)
    ativo = models.BooleanField(default=True, help_text="Falso quando saiu da tabela vigente.")

    class Meta:
        verbose_name = "NCM"
        verbose_name_plural = "NCMs"
        ordering = ["codigo"]

    def __str__(self) -> str:
        from brfiscal.ncm import formatar

        return f"{formatar(self.codigo)} - {self.descricao}"

    @property
    def usavel_em_nota(self) -> bool:
        return len(self.codigo) == 8


class Cest(models.Model):
    codigo = models.CharField(max_length=7, primary_key=True)
    descricao = models.TextField()
    segmento = models.CharField(max_length=200, blank=True)
    item = models.CharField(max_length=20, blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "CEST"
        verbose_name_plural = "CESTs"
        ordering = ["codigo"]

    def __str__(self) -> str:
        from brfiscal.cest import formatar

        return f"{formatar(self.codigo)} - {self.descricao[:80]}"


class CestNcm(models.Model):
    """NCM (ou prefixo de NCM) listado em um CEST."""

    cest = models.ForeignKey(Cest, on_delete=models.CASCADE, related_name="ncms")
    ncm_prefixo = models.CharField(max_length=8, db_index=True)

    class Meta:
        verbose_name = "NCM do CEST"
        verbose_name_plural = "NCMs do CEST"
        constraints = [
            models.UniqueConstraint(fields=["cest", "ncm_prefixo"], name="brfiscal_cest_ncm_unico")
        ]
