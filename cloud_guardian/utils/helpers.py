import ast

def print_function_signatures(file_path):
    """
    Prints the signature of each function defined in the specified Python file.

    :param file_path: Path to the Python file
    """
    with open(file_path, "r") as file:
        source = file.read()
        tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            args = []
            for arg in node.args.args:
                arg_name = arg.arg
                if arg.annotation:
                    # Convert annotation to source code string
                    annotation = ast.unparse(arg.annotation)
                    arg_name += f": {annotation}"
                args.append(arg_name)
                
            # Handle defaults for arguments
            defaults = [ast.unparse(d) for d in node.args.defaults]
            args_with_defaults = [f"{arg}={default}" for arg, default in zip(args[-len(defaults):], defaults)]
            args[:len(args) - len(defaults)] + args_with_defaults
            
            # Concatenate arguments into a string
            args_str = ", ".join(args[:len(args) - len(defaults)] + args_with_defaults)
            
            # Prepare return type
            return_type = f" -> {ast.unparse(node.returns)}" if node.returns else ""
            print(f"def {node.name}({args_str}){return_type}:")

