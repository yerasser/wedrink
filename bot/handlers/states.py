from aiogram.fsm.state import State, StatesGroup


class Flow(StatesGroup):
    idle = State()
    upload_receipt = State()
    edit_item = State()
    add_item = State()