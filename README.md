# Agente de Trading Automatizado com IA

Projeto modular e seguro para análise de mercado e paper trading. **O modo SIMULACAO é obrigatório por padrão; não há garantia de lucro e todo mercado envolve risco de prejuízo.**

## Início rápido

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

O sistema coleta dados, calcula indicadores, registra análises, aplica regras de decisão e valida tudo pelo módulo de risco antes de qualquer execução. O LLM é apenas um fornecedor de insumos e não envia ordens.

## Segurança

- Nunca coloque chaves reais no Git; use `.env` local.
- O modo `REAL` permanece bloqueado por padrão e exige implementação/revisão adicional.
- O módulo de risco é obrigatório para qualquer ordem.
- Este software é educacional e não constitui recomendação financeira.
