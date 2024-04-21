import os
import reflex as rx
import google.generativeai as genai



# Configure the API with your key at the start
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY is not set. Please set the environment variable.")
genai.configure(api_key=api_key)


class QA(rx.Base):
    """A question and answer pair."""

    question: str
    answer: str


DEFAULT_CHATS = {
    "Intros": [],
}


class State(rx.State):
    """The app state."""

    # A dict from the chat name to the list of questions and answers.
    chats: dict[str, list[QA]] = DEFAULT_CHATS

    # The current chat name.
    current_chat = "Intros"

    # The current question.
    question: str

    # Whether we are processing the question.
    processing: bool = False

    # The name of the new chat.
    new_chat_name: str = ""

    def create_chat(self):
        """Create a new chat."""
        # Add the new chat to the list of chats.
        self.current_chat = self.new_chat_name
        self.chats[self.new_chat_name] = []

    def delete_chat(self):
        """Delete the current chat."""
        del self.chats[self.current_chat]
        if len(self.chats) == 0:
            self.chats = DEFAULT_CHATS
        self.current_chat = list(self.chats.keys())[0]

    def set_chat(self, chat_name: str):
        """Set the name of the current chat.

        Args:
            chat_name: The name of the chat.
        """
        self.current_chat = chat_name

    @rx.var
    def chat_titles(self) -> list[str]:
        """Get the list of chat titles.

        Returns:
            The list of chat names.
        """
        return list(self.chats.keys())

    async def process_question(self, form_data: dict[str, str]):
        # Get the question from the form
        question = form_data["question"]

        # Check if the question is empty
        if question == "":
            return

        model = genai.GenerativeModel('gemini-pro')

         # Add the question to the list of questions
        qa = QA(question=question, answer="")
        self.chats[self.current_chat].append(qa)

        # Clear the input and start the processing
        self.processing = True
        yield

        # Get response from Gemini API
        response = model.generate_content(question)

        # Update the last QA pair with the response
        if response.text:
            self.chats[self.current_chat][-1].answer = response.text
        else:
            self.chats[self.current_chat][-1].answer = "No response generated."

        # Toggle the processing flag
        self.processing = False
        self.chats = self.chats
        yield

    async def gemini_process_question(self, question: str):
        """Get the response from the API.

        Args:
            question: the current question
        """

        # Add the question to the list of questions.
        qa = QA(question=question, answer="")
        self.chats[self.current_chat].append(qa)

        # Clear the input and start the processing.
        self.processing = True
        yield

        # Initialize the model from the Gemini API
        model = genai.GenerativeModel('gemini-pro')

        try:
            # Request the model to generate a response
            response = model.generate_content(question)

            # Retrieve the content from the response
            answer_text = response.text if response.text else "No response generated."

        except Exception as e:
            # Handle possible exceptions, e.g., API errors or connection issues
            answer_text = f"An error occurred: {str(e)}"

        # Update the last QA pair with the response
        self.chats[self.current_chat][-1].answer += answer_text
        self.chats = self.chats  # This might be used to trigger updates in some frameworks

        # Toggle the processing flag.
        self.processing = False
        yield
