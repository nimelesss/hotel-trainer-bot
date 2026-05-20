from aiogram.fsm.state import State, StatesGroup


class QuizSG(StatesGroup):
    in_progress = State()
    viewing_explanation = State()


class AdminSG(StatesGroup):
    broadcasting = State()
