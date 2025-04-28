# app/services/pagamento_service.py
from app.models.models import Pagamento

def registrar_pagamento(id_agendamento, data_pagamento, valor, tipo_pagamento):
    novo_pagamento = Pagamento(
        id_agendamento=id_agendamento,
        data_pagamento=data_pagamento,
        valor=valor,
        status='concluido',
        tipo_pagamento=tipo_pagamento
    )
    return novo_pagamento