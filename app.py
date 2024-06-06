# Tkinter Calculator
# 2022/01/14
# https://github.com/BaseMax/TkinterCalculator

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.simpledialog as sd
import shelve as sh
import datetime as dt

# Constants
SHELVE_FILENAME = "calc_shelve.dat"


# Colors
WHITE = "#FFFFFF"
OFF_WHITE = "#F8FAFF"
LABEL_COLOR = "#25265E"
LIGHT_COLOR = "#AAAACC"
HISTORY_FG = "#555599"
LIGHT_BLUE = "#CCEDFF"
LIGHT_GRAY = "#F5F5F5"
MIDDLE_GRAY = "#999999"
DARK_GRAY = "#444444"
BLACK = "#000000"


# Fonts
HISTORY_FONT_STYLE = ("Serif", 8)
DEFAULT_FONT_STYLE = ("Arial", 20)
DIGITS_FONT_STYLE = ("Arial", 24, "bold")
LARGE_FONT_STYLE = ("Arial", 40, "bold")
SMALL_FONT_STYLE = ("Arial", 16)
SMALLER_FONT_STYLE = ("Arial", 12)


# Styles
WHITE_FRAME_STYLE = {
	"bg": WHITE, "borderwidth": 0
}
GRAY_FRAME_STYLE = {
	"bg": LIGHT_GRAY, "borderwidth": 0
}
DIGIT_BUTTON_STYLE = {
	"bg": WHITE, "fg" :LABEL_COLOR, "font": DIGITS_FONT_STYLE, "borderwidth": 0, 
}
OPERATOR_BUTTON_STYLE = {
	"bg": OFF_WHITE, "fg": LABEL_COLOR, "font": DEFAULT_FONT_STYLE, "borderwidth": 0, 
}
DATE_ENTRY_STYLE = {
	"bg": BLACK, "fg": WHITE
}



class TkinterCalculator:

	def __init__(self):
		self.window = tk.Tk()
		self.window.geometry("375x667+900+0")
		self.window.resizable(1, 1)
		self.window.title("Calculator")

		self.expression = ""
		self.result_value = ""
		self.cursor_position = 0
		self.history = []

		self.display_frame = self.create_display_frame()


		self.history_frame, self.history_container, self.history_box = self.create_history_controls()
		self.target_history_box = self.history_box # The tk.Listbox instance that contains all the entries themself.
		
		self.input_frame, self.input_field, self.result_label = self.create_input_controls()

		# Characters that are accepted through keyboard input or/and have virtual keyboard equivalents.
		# This is a map from a character to their corresponding row and column on the virutal keyboard - it it's non the they are not displayed.
		self.characters = {
			7: (1,1),
			8: (1,2),
			9: (1,3),

			4: (2,1),
			5: (2,2),
			6: (2,3),

			1: (3,1),
			2: (3,2),
			3: (3,3),

			0: (4, 2),
			'.':(4, 1),
			',':(4,3),
			"=": None,
		}
		# Append all alpha numeric characters to the acceptable characters table:
		for ascii in range(0,128):
			character = chr(ascii)
			if character.isalpha():
				self.characters[character] = None

		self.operands = {
			"/": "\u00F7",
			"*": "\u00D7",
			"-": "-",
			"+": "+",
			"=": "="
		}


		self.buttons_frame = self.create_buttons_frame()

		self.buttons_frame.rowconfigure(0, weight=1)
		for x in range(1, 5):
			self.buttons_frame.rowconfigure(x, weight=1)
			self.buttons_frame.columnconfigure(x, weight=1)

		self.create_digit_buttons()
		self.create_operator_buttons()
		self.create_special_buttons()
		self.bind_keys()

		self.load_history()
		self.history_window = None


	def run(self):
		self.window.bind("<FocusIn>", self.handle_focus)
		self.input_field.focus_set()
		self.window.mainloop()

	def handle_focus(self, event):
		self.input_field.focus_set()

	## User Interface creation logic ##
		
	def create_display_frame(self):
		frame = tk.Frame(self.window, height=221, bg=LIGHT_GRAY)
		frame.pack(expand=True, fill="both")
		return frame


	def create_history_controls(self, parent = None, docked = True):
		if parent == None:
			parent = self.display_frame

		if docked:
			history_frame = tk.Frame(parent , padx=0, pady=2, bg=WHITE, borderwidth=1, relief="flat", highlightbackground=MIDDLE_GRAY, highlightthickness=0)
			history_frame.pack(fill='both', expand=False, padx=4, pady=2)
		else:
			history_frame = tk.Frame(parent , padx=0, pady=2, bg=WHITE, borderwidth=1, relief="flat", highlightbackground=MIDDLE_GRAY, highlightthickness=0)
			history_frame.pack(fill='both', expand=True)


		## The header of the history panel:
		header_frame = tk.Frame(history_frame, **WHITE_FRAME_STYLE)
		header_frame.grid(row=0, column=0, sticky=tk.NSEW)

		if docked:
			# The history button:
			image = tk.PhotoImage(file="clock.png")
			undock_button = tk.Button(header_frame, image=image, relief="flat", border=0, command=self.toggle_history_box)
			undock_button.image = image
			undock_button.grid(row=0, column=0, sticky=tk.W, padx=2, pady=2)

			# The undock button:
			image = tk.PhotoImage(file="undock.png")
			undock_button = tk.Button(header_frame, image=image, relief="flat", border=0, command=self.undock_history)
			undock_button.image = image
			undock_button.grid(row=0, column=1, sticky=tk.W, padx=2, pady=2)

		history_label = tk.Label(header_frame, text="History of computations", font=SMALLER_FONT_STYLE, bg=WHITE, fg=BLACK, border=0)
		if docked:
			history_label.grid(row=0, column=2, padx=4, sticky=tk.EW)
		else:
			history_label.grid(row=0, column=0, columnspan=2, padx=4, sticky=tk.EW)

		history_frame.rowconfigure(1, weight=1)
		history_frame.columnconfigure(0, weight=1)


		## The history container for the separator and the history entries listbox itself:
		history_container = tk.Frame(history_frame, **WHITE_FRAME_STYLE)
		history_container.grid(row=1, column=0, columnspan=2, sticky=tk.NSEW)
		
		if docked:
			history_container.visible = True # Add a property that indicate whether own history box is visible (when docked).

		# Separator from the header:
		separator = tk.Frame(history_container, bg=LIGHT_GRAY, height=1)
		separator.grid(row=0, column=0, sticky=tk.EW, pady=3, padx=0)

		history_box = tk.Listbox(history_container, width=None, height=6 if docked else 40,
						   border=0, highlightthickness=0, highlightcolor=LIGHT_GRAY, 
						   font=HISTORY_FONT_STYLE, bg=WHITE, fg=BLACK, selectbackground=DARK_GRAY, )
		
		history_container.rowconfigure(1, weight=1)
		history_container.columnconfigure(0, weight=1)

		history_box.grid(padx=6, pady=4, row=1, column=0, sticky=tk.NSEW)
		history_box.bind("<Double-1>", self.enter_history_item)

		return history_frame, history_container, history_box


	def create_input_controls(self):
		input_frame = tk.Frame(self.display_frame, **GRAY_FRAME_STYLE)
		input_frame.pack(expand=True, fill="x")

		def validator(param):
			all_input = {}
			all_input.update(self.characters)
			all_input.update(self.operands)

			for character in param:
				for allowed_char in all_input:
					if allowed_char == character: return True
			return False

		validate_command = (self.window.register(validator))
		input_field = tk.Entry(input_frame, validate="all", validatecommand=(validate_command, "%P"), justify=tk.RIGHT, border=0, font=SMALL_FONT_STYLE, bg=LIGHT_GRAY, fg=LABEL_COLOR)
		input_field.pack(expand=True, fill='both', padx=24)


		total_label = tk.Label(input_frame, text="", anchor=tk.E, padx=24, font=LARGE_FONT_STYLE, bg=LIGHT_GRAY, fg=LABEL_COLOR)
		total_label.pack(expand=True, fill='both')

		return input_frame, input_field, total_label


	def create_buttons_frame(self):
		frame = tk.Frame(self.window)
		frame.pack(expand=True, fill="both")
		return frame


	def create_special_buttons(self):
		self.create_clear_button()
		self.create_square_button()
		self.create_sqrt_button()
		self.create_equals_button()


	def create_clear_button(self):
		button = tk.Button(self.buttons_frame, text="C", command=self.clear, **OPERATOR_BUTTON_STYLE)
		button.grid(row=0, column=1, sticky=tk.NSEW)


	def create_square_button(self):
		button = tk.Button(self.buttons_frame, text="x\u00b2", command=self.square, **OPERATOR_BUTTON_STYLE)
		button.grid(row=0, column=2, sticky=tk.NSEW)


	def create_sqrt_button(self):
		button = tk.Button(self.buttons_frame, text="\u221ax", command=self.sqrt, **OPERATOR_BUTTON_STYLE)
		button.grid(row=0, column=3, sticky=tk.NSEW)


	def create_operator_buttons(self):
		i = 0
		for operator, symbol in self.operands.items():
			button = tk.Button(self.buttons_frame, text=symbol, command=lambda x=operator: self.append_operator(x), **OPERATOR_BUTTON_STYLE)
			button.grid(row=i, column=4, sticky=tk.NSEW)
			i += 1


	def create_digit_buttons(self):
		for digit, grid_value in self.characters.items():
			if grid_value == None: continue # Skip the characters that have no virutal keys representation.
			button = tk.Button(self.buttons_frame, text=str(digit),  command=lambda x=digit: self.add_to_expression(x), **DIGIT_BUTTON_STYLE,)
			button.grid(row=grid_value[0], column=grid_value[1], sticky=tk.NSEW)


	def create_equals_button(self):
		button = tk.Button(self.buttons_frame, text="=", bg=LIGHT_BLUE, fg=LABEL_COLOR, font=DEFAULT_FONT_STYLE, borderwidth=0, command=self.evaluate)
		button.grid(row=4, column=3, columnspan=2, sticky=tk.NSEW)


	# Handle
	def bind_keys(self):
		def on_enter_press(event):
			self.evaluate()
			self.write_to_history()
			self.input_field.delete(0, tk.END)

		self.window.bind("<Return>", on_enter_press)
		self.window.bind("<BackSpace>", self.on_backspace)

		all_input = {}
		all_input.update(self.characters)
		all_input.update(self.operands)


		def handle_input(event):
			self.update_input_field()
			self.evaluate()

		for key in all_input:
			self.window.bind(str(key), lambda event, key=key: handle_input(key))


		
	def on_backspace(self):
		self.expression


	def clear(self):
		self.expression = ""
		self.update_input_field()
		self.update_result_label()


	def square(self):
		if self.expression:
			self.expression = f"({self.expression})**2"
			self.update_input_field()
			self.evaluate()


	def sqrt(self):
		if self.expression:
			self.expression = f"({self.expression})**0.5"
			self.update_input_field()
			self.evaluate()


	def toggle_history_box(self):
		if self.history_container.visible:
			self.history_container.grid_forget()
		else:
			self.history_container.grid(row=2,column=0, padx=4, sticky=tk.EW)
		self.history_container.visible = not self.history_container.visible


	def undock_history(self):
		self.history_frame.pack_forget()
		self.history_window = HistoryWindow(self)
		self.load_history()


	def dock_history(self):
		self.history_frame.pack(side="top", expand=True, fill="both", padx=10, pady=10)
		self.input_frame.pack(side="bottom", expand=True, fill="both")
		self.target_history_box = self.history_box
		self.load_history()
		

	# Update
	def update_input_field(self):
		self.symbols = {
			"/": "/",
			"*": "*",
			"-": "-",
			"+": "+",
			"=": "=",
			"*  *": "**"
		}

		# expression = self.total_expression
		expression = self.input_field.get()

		# Since the last call made spaces around operators - now we need to clear them 
		# before applying them again:
		expression = expression.replace(" ", "") 
		for operator, symbol in self.symbols.items():
			expression = expression.replace(operator, f' {symbol} ') 

		self.expression = expression

		self.input_field.delete(0, tk.END)
		self.input_field.insert(tk.END, expression)

	def update_result_label(self):
		self.result_label.config(text=self.result_value)


	# Evaluate
	def evaluate(self, results = {}):
		expression = self.input_field.get()
		try:
			exec("result = " + expression, globals(), results)
			self.result_value = str(results["result"])
		except Exception as e:
			print(e)
			self.result_value = "Error"
		finally:
			self.update_result_label()


	def enter_history_item(self, event):
		''' Fired when history item is double clicked ''' 
		selected_entry = self.history_box.selection_get()

		selected_expression = selected_entry.split("=")[0]

		self.expression = selected_expression
		self.update_input_field()
		self.evaluate()


	def write_to_history(self):
		if self.result_value != "Error":
			total_expression = self.expression
			# for operator, symbol in self.operations.items():
			# 	total_expression = total_expression.replace(operator, " " + symbol + " ")

			expression_with_result = total_expression + " = " + self.result_value
			self.target_history_box.insert(tk.END, expression_with_result)
			self.target_history_box.yview(tk.END)
			self.expression = ""
			self.update_input_field()
			self.update_result_label()

			datetime_str = dt.datetime.now().strftime("%d-%m-%Y %H:%M")
			history_entry = datetime_str + " " + expression_with_result
			self.history.append(history_entry)

			with sh.open(SHELVE_FILENAME) as shelve:
				shelve["history"] = self.history
				

	def load_history(self, target_history_listbox = None):
		if target_history_listbox == None:
			target_history_listbox = self.target_history_box

		try:
			with sh.open(SHELVE_FILENAME) as shelve:
				self.history = shelve["history"] 

				dates = []
				for history_entry in self.history:
					datetime_str = history_entry[0:16]
					datetime_obj = dt.datetime.strptime(datetime_str, "%d-%m-%Y %H:%M").timestamp()
					date_obj = dt.date.fromtimestamp(datetime_obj)
					today = dt.date.today()
					delta = today - date_obj
					print(delta.days)

					if delta.days == 0:
						header = " Today"
					elif delta.days == 1:
						header = " Yesterday"
					else:
						header = date_obj.strftime(" %d-%m-%Y, %A")

					if not date_obj in dates:
						self.target_history_box.insert(tk.END, header)
						self.target_history_box.itemconfig(tk.END, **DATE_ENTRY_STYLE)

						dates.append(date_obj)

					expression = history_entry[16:]
					self.target_history_box.insert(tk.END, expression.strip())
					self.target_history_box.yview(tk.END)
		except KeyError:
			print("No history file or history not written")



class HistoryWindow(tk.Toplevel):
	def __init__(self, app : TkinterCalculator):
		super().__init__(app.window)
		self.app = app

		self.history_frame, self.history_container, self.history_box = self.app.create_history_controls(parent=self, docked=False)
		self.app.target_history_box = self.history_box		


	def destroy(self) -> None:
		super().destroy()
		self.app.dock_history()


''' Run the script if we're main '''
if __name__ == "__main__":
	tkinter_calculator = TkinterCalculator()
	tkinter_calculator.run()
