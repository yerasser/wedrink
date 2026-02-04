from aiogram.fsm.state import State, StatesGroup

class DraftEdit(StatesGroup):
    editing = State()
