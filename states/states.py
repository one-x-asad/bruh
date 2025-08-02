from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from loader import dp, bot

dp.storage = MemoryStorage()

# Statelar
class FillStars(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_amount = State()
