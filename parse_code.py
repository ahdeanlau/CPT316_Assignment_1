import re

# Define the token types and regex patterns
token_specification = [
    ("INTEGER", r"\d+"),  # Integer
    ("OPERATOR", r"[+\-*/=]"),  # Arithmetic operators
    ("IDENTIFIER", r"[a-zA-Z_]\w*"),  # Identifiers
    ("LPAREN", r"\("),  # Left parenthesis
    ("RPAREN", r"\)"),  # Right parenthesis
    ("SEMICOLON", r";"),  # Semicolon
    ("SKIP", r"[ \t]+"),  # Skip over spaces and tabs
    ("MISMATCH", r"."),  # Any other character
]

# Create a regex that matches any of the tokens
tok_regex = "|".join("(?P<%s>%s)" % pair for pair in token_specification)


# The lexer function
def lexer(code):
    tokens = []

    # For each match, create a token
    for mo in re.finditer(tok_regex, code):
        # Get the token type and value
        kind = mo.lastgroup
        value = mo.group()
        
        # Skip over spaces and tabs
        if kind == "SKIP":
            continue
        # Raise an error if the token is illegal
        elif kind == "MISMATCH":
            raise RuntimeError(f"Illegal character {value!r}")
        else:
            # Create a token and add it to the list
            if kind == "INTEGER":
                value = int(value)  # Convert string to integer
            tokens.append((kind, value))
    return tokens


# -----------------------------------------------------------------------------------------

# Define the AST node class
class ASTNode:
    # The constructor, with a default value of None for the left and right children
    def __init__(self, type, value=None, left=None, right=None):
        self.type = type
        self.value = value
        self.left = left
        self.right = right

    # The string representation of the node
    def __repr__(self):
        if self.type == "BINARY_OP":
            return f"({self.left} {self.value} {self.right})"
        elif self.type == "ASSIGNMENT":
            return f"({self.value} = {self.right})"
        else:
            return f"({self.type}: {self.value})"
    
    # Display the tree in a human-readable format with indentation
    def display_tree(self, level=0):
        indentation = '  ' * level
        if self.type == 'BINARY_OP':
            print(f'{indentation}OP: {self.value}')
            self.left.display_tree(level + 1)
            self.right.display_tree(level + 1)
        elif self.type == 'ASSIGNMENT':
            print(f'{indentation}ASSIGNMENT: {self.value} =')
            self.right.display_tree(level + 1)
        else:
            print(f'{indentation}{self.type}: {self.value}')
    
    # Output the GraphViz dot file of the tree
    def to_dot(self, parent_id, dot_str):
        if self.type == 'BINARY_OP':
            node_id = f'node{len(dot_str)}'
            dot_str.append(f'{node_id} [label="BINARY_OP: {self.value}"];\n')
            dot_str.append(f'{parent_id} -> {node_id};\n')
            self.left.to_dot(node_id, dot_str)
            self.right.to_dot(node_id, dot_str)
        elif self.type == 'ASSIGNMENT':
            node_id = f'node{len(dot_str)}'
            dot_str.append(f'{node_id} [label="ASSIGNMENT: ="];\n')  # Updated label
            
            left_node_id = f'node{len(dot_str)}'
            dot_str.append(f'{left_node_id} [label="IDENTIFIER: {self.value}"];\n')
            dot_str.append(f'{node_id} -> {left_node_id};\n')
            
            self.right.to_dot(node_id, dot_str)
        else:
            node_id = f'node{len(dot_str)}'
            dot_str.append(f'{node_id} [label="{self.type}: {self.value}"];\n')
            dot_str.append(f'{parent_id} -> {node_id};\n')

# Define the parser class
class Parser:
    def __init__(self, tokens):  # Takes a list of tokens
        self.tokens = tokens  # Store the tokens
        self.position = 0

    # Returns the next token without consuming it
    def lookahead(self):
        if self.position < len(self.tokens):  # Check that we haven't reached the end
            return self.tokens[self.position]  # Return the next token
        else:
            return None

    # Consumes the next token and checks its type
    def consume(self, expected_type):
        if (
            self.lookahead() and self.lookahead()[0] == expected_type
        ):  # Check that we haven't reached the end and that the next token is the expected type
            self.position += 1
            return self.tokens[self.position - 1]
        else:
            raise RuntimeError(
                f"Expected token type {expected_type}, got {self.lookahead()} at {self.position}"
            )

    # Parses a factor
    # factor = integer | identifier | "(" expression ")"
    def factor(self):
        token = self.lookahead()
        if token[0] == "INTEGER":
            self.consume("INTEGER")
            return ASTNode("INTEGER", token[1])
        elif token[0] == "LPAREN":
            self.consume("LPAREN")
            node = self.expression()
            self.consume("RPAREN")
            return node
        elif token[0] == "IDENTIFIER":
            self.consume("IDENTIFIER")
            return ASTNode("IDENTIFIER", token[1])
        else:
            raise RuntimeError("Expected integer, identifier, or parenthesis")

    # Parses a term
    # term = factor { ("*" | "/") factor }
    def term(self):
        node = self.factor()
        while (
            self.lookahead()
            and self.lookahead()[0] == "OPERATOR"
            and self.lookahead()[1] in ("*", "/")
        ):
            op = self.consume("OPERATOR")[1]
            right = self.factor()
            node = ASTNode("BINARY_OP", op, left=node, right=right)
        return node

    # Parses an expression
    # expression = term { ("+" | "-") term }
    def expression(self):
        node = self.term()
        while (
            self.lookahead()
            and self.lookahead()[0] == "OPERATOR"
            and self.lookahead()[1] in ("+", "-")
        ):
            op = self.consume("OPERATOR")[1]
            right = self.term()
            node = ASTNode("BINARY_OP", op, left=node, right=right)
        return node

    # Parses an assignment
    # assignment = identifier "=" expression
    def assignment(self):
        identifier = self.consume("IDENTIFIER")
        self.consume("OPERATOR")  # We assume that the operator is '='
        expr = self.expression()
        return ASTNode("ASSIGNMENT", value=identifier[1], left=None, right=expr)

    # Parses the program
    # program = assignment ";"
    def parse(self):
        node = self.assignment()
        # Must be semicolon at the end
        if self.lookahead() and self.lookahead()[0] == "SEMICOLON":
            self.consume("SEMICOLON")
        return node


# Function to check the syntax
def check_syntax(code):
    try:
        # Run the lexer and parser
        tokens = lexer(code)
        parser = Parser(tokens)
        parsed_tree = parser.parse()

        # Display the tree
        print(parsed_tree)
        parsed_tree.display_tree()

        # Output the GraphViz dot file
        dot_str = ['digraph SyntaxTree {\n']
        parsed_tree.to_dot('root', dot_str)
        dot_str.append('}\n')

        with open('syntax_tree.dot', 'w') as dot_file:
            dot_file.writelines(dot_str)

        return "Syntax is acceptable. Dot file is created."
    except RuntimeError as e:
        return f"Syntax error: {e}"


# Prompt for user input
code_input = input("Enter your code: ")
# print(check_syntax(code_input))

# Sample input
print(check_syntax("x = 2 * 3 + ((4 - 1) * 6) - (x - 5) = x;"))
