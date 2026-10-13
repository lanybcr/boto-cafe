"""Ponto de entrada da Fase 1: gera dados, grava SQLite + CSVs e valida.

Uso (na raiz do projeto):
    python -m src.gerar_dados
"""
from . import banco, gerador, validacao


def main() -> None:
    dados = gerador.gerar_tudo()
    banco.salvar_sqlite(dados)
    banco.exportar_csvs(dados)

    for tabela in banco.TABELAS:
        print(f"{tabela:<14} {len(dados[tabela]):>7,} linhas")

    resultado = validacao.validar_integridade()
    print("\n", resultado.to_string(index=False))
    if not resultado["ok"].all():
        raise SystemExit("Falha na validação de integridade!")
    print("\nIntegridade OK.")


if __name__ == "__main__":
    main()
