from django.contrib import admin

from .models import Cest, CestNcm, Ncm, VersaoTabela


@admin.register(Ncm)
class NcmAdmin(admin.ModelAdmin):
    list_display = ["codigo", "descricao", "ativo"]
    list_filter = ["ativo"]
    search_fields = ["codigo", "descricao_completa"]


class CestNcmInline(admin.TabularInline):
    model = CestNcm
    extra = 0


@admin.register(Cest)
class CestAdmin(admin.ModelAdmin):
    list_display = ["codigo", "descricao", "segmento", "ativo"]
    list_filter = ["segmento", "ativo"]
    search_fields = ["codigo", "descricao", "ncms__ncm_prefixo"]
    inlines = [CestNcmInline]


@admin.register(VersaoTabela)
class VersaoTabelaAdmin(admin.ModelAdmin):
    list_display = ["tabela", "vigencia", "ato", "total", "carregada_em"]
