"""Shim de compatibilidade — redireciona imports antigos para core.electrical.

ATENÇÃO: Este arquivo existe apenas para não quebrar código externo ou
testes que ainda referenciem 'models.rooms'. Novos módulos devem
importar diretamente de 'core.electrical.rooms'.
"""
from core.electrical.rooms import Kitchen, Bedroom, Bathroom, Living, Corridor, Garage, LivingKitchen

__all__ = ["Kitchen", "Bedroom", "Bathroom", "Living", "Corridor", "Garage", "LivingKitchen"]
