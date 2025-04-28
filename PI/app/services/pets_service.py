# app/services/pets_service.py
from app.models.models import Pet

def criar_pet(id_usuario, nome_pet, raca, idade, sexo, peso, castrado, alimentacao, saude):
    novo_pet = Pet(
        id_usuario=id_usuario,
        nome_pet=nome_pet,
        raca=raca,
        idade=idade,
        sexo=sexo,
        peso=peso,
        castrado=castrado,
        alimentacao=alimentacao,
        saude=saude
    )
    return novo_pet