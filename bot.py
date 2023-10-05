import os
import random
import mysql.connector
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler

# Import your database and token reader functions
from database.database_config import get_database_connection
from config.token_reader import get_bot_token

# Retrieve the Telegram bot token from the token.txt file
TOKEN = get_bot_token()

# Establish a database connection using the function from database_config.py
db_connection = get_database_connection()

# Initialize a dictionary to store user scores
user_scores = {}

# Start command handler


def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id

    # Fetch quiz questions from the database
    cursor = db_connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM quiz_questions")
    quiz_questions = cursor.fetchall()

    if not quiz_questions:
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="No quiz questions available.")
        return

    # Shuffle the quiz questions
    random.shuffle(quiz_questions)

    # Create a list to store user's answers
    user_answers = []

    for question_data in quiz_questions:
        # Create inline keyboard buttons for quiz options
        options = [
            InlineKeyboardButton(
                "1. " + question_data["option1"], callback_data="1"),
            InlineKeyboardButton(
                "2. " + question_data["option2"], callback_data="2"),
            InlineKeyboardButton(
                "3. " + question_data["option3"], callback_data="3"),
            InlineKeyboardButton(
                "4. " + question_data["option4"], callback_data="4"),
        ]

        # Create an inline keyboard markup
        reply_markup = InlineKeyboardMarkup([options])

        # Send the quiz question with options
        message = context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=question_data["question"],
            reply_markup=reply_markup,
        )

        user_answers.append({
            "message_id": message.message_id,
            "correct_option": question_data["correct_option"]
        })

    # Store the user's answers for later checking
    user_scores[user_id] = {
        "score": 0,
        "user_answers": user_answers,
        "current_question": 0
    }

# Callback function to handle user answers


def answer_quiz(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    user_data = user_scores.get(user_id)

    if user_data is not None and user_data["current_question"] < len(user_data["user_answers"]):
        current_question_index = user_data["current_question"]
        user_answer = int(query.data)
        correct_option = user_data["user_answers"][current_question_index]["correct_option"]

        if user_answer == correct_option:
            user_data["score"] += 1

        # Next question
        current_question_index += 1
        user_data["current_question"] = current_question_index

        # Check if there are more questions
        if current_question_index < len(user_data["user_answers"]):
            question_data = user_data["user_answers"][current_question_index]
            options = [
                InlineKeyboardButton(
                    "1. " + question_data["option1"], callback_data="1"),
                InlineKeyboardButton(
                    "2. " + question_data["option2"], callback_data="2"),
                InlineKeyboardButton(
                    "3. " + question_data["option3"], callback_data="3"),
                InlineKeyboardButton(
                    "4. " + question_data["option4"], callback_data="4"),
            ]

            reply_markup = InlineKeyboardMarkup([options])
            context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=query.message.message_id,
                text=question_data["question"],
                reply_markup=reply_markup,
            )
        else:
            final_score = user_data["score"]
            context.bot.send_message(
                chat_id=update.effective_chat.id, text=f"Your final score: {final_score}")
            del user_scores[user_id]

    # Answer the callback query to remove the inline keyboard
    query.answer()

# Set up the Telegram bot and handlers


def main():
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(answer_quiz))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
