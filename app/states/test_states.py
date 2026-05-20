from aiogram.fsm.state import State, StatesGroup


class QuizSG(StatesGroup):
    choosing_topic = State()
    in_progress = State()
    viewing_explanation = State()


class AdminSG(StatesGroup):
    broadcasting = State()
