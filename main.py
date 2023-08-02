#код))
#впервые работаю с состояниями. посмотрим, что выйдет
from aiogram import types, executor, Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import TOKEN, ADMIN_ID

storage = MemoryStorage
bot = Bot(TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


class ApplicationStatesGroup(StatesGroup):

    name = State()
    tel = State()
    address = State()
    description = State()
    photo = State()


def get_kb(my_list) -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for i in my_list:
        kb.add(KeyboardButton(i))
    return kb


@dp.message_handler(commands=['cancel'], state='*')
async def ap_cancel(message: types.Message, state: FSMContext):
    if state is None:
        return

    await state.finish()
    await message.answer('Вы прервали создание заявки',
                         reply_markup=get_kb(['/create_application']))


@dp.message_handler(commands=['start'])
async def ha_start(message: types.Message) -> None:
    await message.answer('Добро пожаловать! Чтобы отправить заявку, нажми /create_application ниже',
                         reply_markup=get_kb(['/create_application']))


@dp.message_handler(commands=['create_application'])
async def ha_create_application(message: types.Message) -> None:
    await message.answer('Для начала, напиши мне, как я могу к тебе обращаться',
                         reply_markup=get_kb(['/cancel']))
    await ApplicationStatesGroup.name.set()


@dp.message_handler(state=ApplicationStatesGroup.name)
async def load_name(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['name'] = message.text
    await message.answer('Напиши номер, по которому следует звонить в фомате: +7**********')
    await ApplicationStatesGroup.next()


@dp.message_handler(lambda message: (len(message.text) != 12) or (message.text[0:2] != '+7') or
                                    (not message.text[1:].isdigit()),
                    state=ApplicationStatesGroup.tel)
async def check_tel(message: types.Message):
    await message.reply('Это не телефон!')


@dp.message_handler(state=ApplicationStatesGroup.tel)
async def load_tel(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['tel'] = message.text
    await message.answer('Напиши адрес, где случились проблемы в формате:\n' +
                         'Город, улица, дом, квартира')
    await ApplicationStatesGroup.next()


@dp.message_handler(state=ApplicationStatesGroup.address)
async def load_address(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['address'] = message.text
    await message.answer('Напиши кратко, в одно сообщение, что случилось')
    await ApplicationStatesGroup.next()


@dp.message_handler(state=ApplicationStatesGroup.description)
async def load_description(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['description'] = message.text
    await message.answer('Добавь фотографию этикетки с серийным номером техники.' +
                         ' Если таковой нет, сфотографируй целиком сломавшийся прибор')
    await ApplicationStatesGroup.next()


@dp.message_handler(lambda message: not message.photo, state=ApplicationStatesGroup.photo)
async def check_photo(message: types.Message):
    await message.reply('Это не фото!')


@dp.message_handler(content_types=['photo'], state=ApplicationStatesGroup.photo)
async def load_photo(message: types.Message, state: FSMContext) -> None:
    async with state.proxy() as data:
        data['photo'] = message.photo[0].file_id
        await bot.send_photo(chat_id=ADMIN_ID,
                             photo=data['photo'],
                             caption=f"Новая заявка!\nИмя: {data['name']}\nТелефон: {data['tel']}\n" +
                                     f"Адрес: {data['address']}\nОписание: {data['description']}")
    await message.answer('Ваша заявка принята, ожидайте ответ!')
    await state.finish()


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)


