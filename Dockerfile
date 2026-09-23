# GAEA · imagem de produção
# Sem dependência externa: o app é stdlib. Roda como usuário sem privilégio,
# com o banco num volume — o container continua descartável (27002 8.9, 8.31).
FROM python:3.12-slim

RUN useradd --create-home --uid 10001 gaea
WORKDIR /app
COPY --chown=gaea:gaea . /app
RUN rm -rf servidor/dados .git .claude && mkdir -p /dados && chown gaea:gaea /dados

USER gaea
ENV GAEA_MODO=producao \
    GAEA_HOST=0.0.0.0 \
    GAEA_PORTA=8080 \
    GAEA_BANCO=/dados/gaea.db \
    GAEA_TLS_BORDA=1 \
    PYTHONUNBUFFERED=1
# GAEA_SEGREDO, GAEA_ORIGEM e GAEA_ADMIN_TOKEN vêm do orquestrador, nunca da imagem
VOLUME ["/dados"]
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/api/saude',timeout=4).status==200 else 1)"
CMD ["python", "servidor/gaea_api.py"]
