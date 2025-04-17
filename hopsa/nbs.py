"""Utilities for working with notebooks"""

# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/nbs.ipynb.

# %% auto 0
__all__ = ['pydantic_to_markdown_table', 'print_dict_structure', 'export_ipynb_yaml', 'export_ipynb_toml']

# %% ../nbs/nbs.ipynb 3
import inspect
import nbformat
import yaml
from pathlib import Path
from typing import Type, Any, Optional, Dict, get_type_hints, get_origin, get_args
from pydantic import BaseModel, Field
from IPython.display import display, Markdown


# %% ../nbs/nbs.ipynb 5
def _format_type(type_hint: Any) -> str:
    """Format a type hint into a readable string."""
    if get_origin(type_hint) is not None:
        # Handle generic types like List[str], Optional[int], etc.
        origin = get_origin(type_hint)
        args = get_args(type_hint)
        
        if origin is Union:
            # Handle Optional (Union[X, None])
            if len(args) == 2 and args[1] is type(None):
                return f"Optional[{_format_type(args[0])}]"
            else:
                return f"Union[{', '.join(_format_type(arg) for arg in args)}]"
        
        # Handle other generic types
        origin_name = origin.__name__ if hasattr(origin, "__name__") else str(origin).replace("typing.", "")
        args_str = ", ".join(_format_type(arg) for arg in args)
        return f"{origin_name}[{args_str}]"
    
    # Handle non-generic types
    if hasattr(type_hint, "__name__"):
        return type_hint.__name__
    
    return str(type_hint).replace("typing.", "")

# %% ../nbs/nbs.ipynb 6
def _escape_table_cell(text: str) -> str:
    """
    Escape special characters in markdown table cells.
    The key is to escape pipe characters with HTML entity or backslash.
    """
    if not isinstance(text, str):
        text = str(text)
    
    # Replace pipe characters with HTML entity
    # This is the most reliable way to prevent them from being interpreted as column separators
    return text.replace("|", "\|")

# %% ../nbs/nbs.ipynb 7
def pydantic_to_markdown_table(model_class: Type[BaseModel]) -> None:
    """
    Convert a Pydantic model class to a markdown table and display it in Jupyter notebook.
    
    Args:
        model_class: A Pydantic model class (subclass of BaseModel)
    """
    if not issubclass(model_class, BaseModel):
        raise TypeError("Input must be a Pydantic BaseModel class")
    
    md_name = f"## {model_class.__name__}\n"
    md_docstring = f"{inspect.getdoc(model_class)}\n" or ""
    
    # Get source code lines to extract comments
    try:
        source_lines = inspect.getsource(model_class).splitlines()
    except (OSError, TypeError):
        source_lines = []
    
    # Extract property comments from source code
    property_comments = {}
    for i, line in enumerate(source_lines):
        if ":" in line and "#" in line:
            # Extract property name and comment
            property_part = line.split(":")[0].strip()
            comment_part = line.split("#")[1].strip()
            property_comments[property_part] = comment_part
    
    # Start building the markdown table
    table = "\n| Variable | Type | Default | Details |\n"
    table += "|---|---|---|---|\n"
    
    # Get type hints and model fields
    type_hints = get_type_hints(model_class)
    
    # Handle both Pydantic v1 and v2
    model_fields = getattr(model_class, "model_fields", None)
    if model_fields is None:
        model_fields = getattr(model_class, "__fields__", {})
    
    # Process each field
    for field_name, field_type in type_hints.items():
        # Skip private fields and methods
        if field_name.startswith('_'):
            continue
        
        # Get field info
        field_info = None
        if model_fields and field_name in model_fields:
            field_info = model_fields[field_name]
        
        # Format type string
        type_str = _format_type(field_type)
        
        # Get default value
        default_value = "..."  # Pydantic's notation for required fields
        
        # Try to get default from field info
        if field_info:
            # For Pydantic v2
            if hasattr(field_info, "default") and field_info.default is not inspect.Signature.empty:
                default_value = _escape_table_cell(repr(field_info.default))
            # For Pydantic v1
            elif hasattr(field_info, "default") and not field_info.required:
                default_value = _escape_table_cell(repr(field_info.default))
        
        # Get description
        description = ""
        
        # Try to get description from Field
        if field_info and hasattr(field_info, "description") and field_info.description:
            description = _escape_table_cell(field_info.description)
        # Fallback to comment
        elif field_name in property_comments:
            description = _escape_table_cell(property_comments[field_name])
        
        # For nested Pydantic models, add a reference note
        if issubclass(field_type, BaseModel) if isinstance(field_type, type) else False:
            description += f" (see `{field_type.__name__}` table)"
        
        # Add row to table
        table += f"| `{field_name}` | `{type_str}` | {default_value} | {description} |\n"
    
    return display(Markdown(md_name + md_docstring + table))

# %% ../nbs/nbs.ipynb 13
def print_dict_structure(
    d: Dict, # The dictionary that will be pretty printed
    indent=0 # The indent that is used for subkeys
    ) -> str:
    for key, value in d.items():
        print("  " * indent + f"├── {key}")
        if isinstance(value, dict):
            print_dict_structure(value, indent + 1)

# %% ../nbs/nbs.ipynb 18
def export_ipynb_yaml(
    nb_path: Optional[str] = None,
    output_path: Optional[str] = None
    ) -> None:
    """
    Export the content of the current Jupyter notebook to a YAML file.
    
    This function reads the content of the notebook where it's being executed,
    extracts all level 2 (##) markdown cells as groups, and all code cells as
    key-value pairs within those groups. Regular text markdown cells are ignored.
    
    Parameters:
    -----------
    nb_path : str, optional
        Path to the notebook file. If None, the function will try to determin the
        current notebook path automatically (works in standard Jupyter but may not
        work in all environments like VS Code).
    output_path : str, optional
        Path where the YAML file should be saved. If None, the YAML file will be
        saved in the same directory as the notebook with the same name but with
        a .yaml extension.
    
    Returns:
    --------
    None
    """
        # Get the path of the notebook that's currently being executed if not provided
    if nb_path is None:
        try:
            import IPython
            ipython = IPython.get_ipython()
            # Try different methods to get the notebook path
            if hasattr(ipython, 'kernel') and hasattr(ipython.kernel, 'path'):
                nb_path = ipython.kernel.path
            elif hasattr(ipython, 'ev'):
                # Try to get the path from the %notebook magic command history
                for line in ipython.history_manager.get_tail(100, include_latest=True):
                    if '%notebook' in line[2]:
                        parts = line[2].split()
                        for i, part in enumerate(parts):
                            if part == '%notebook' and i+1 < len(parts):
                                nb_path = parts[i+1]
                                break
        except (ImportError, AttributeError):
            pass
        
        if nb_path is None:
            raise ValueError(
                "Could not determine the notebook path automatically. "
                "Please provide the notebook_path parameter explicitly."
            )
    
    # Read the notebook
    with open(nb_path, 'r', encoding='utf-8') as f:
        notebook = nbformat.read(f, as_version=4)
    
    # Initialize variables
    yaml_data = {}
    current_group = None
    
    # Process cells
    for cell in notebook.cells:
        # Process markdown cells to find level 2 headings
        if cell.cell_type == 'markdown':
            lines = cell.source.split('\n')
            for line in lines:
                if line.startswith('## '):
                    # Found a level 2 heading, use it as a group
                    current_group = line[3:].strip()
                    yaml_data[current_group] = {}
        
        # Process code cells if we have a current group
        elif cell.cell_type == 'code' and current_group is not None:
            # Process each line in the code cell looking for parameter assignments
            code_lines = cell.source.split('\n')
            for line in code_lines:
                # Skip empty lines and comments
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Look for parameter assignments (var = value)
                if '=' in line:
                    # Skip line that calls this export function
                    if 'export_ipynb_yaml' in line:
                        continue

                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value_str = parts[1].strip()
                        
                        # Try to evaluate the value to get proper types
                        try:
                            # Handle string values that might be quoted
                            if (value_str.startswith('"') and value_str.endswith('"')) or \
                               (value_str.startswith("'") and value_str.endswith("'")):
                                value = value_str[1:-1]  # Remove quotes
                            else:
                                # Try to evaluate as Python literal
                                import ast
                                value = ast.literal_eval(value_str)
                        except (SyntaxError, ValueError):
                            # If evaluation fails, use the string as is
                            value = value_str
                        
                        # Add to YAML data
                        yaml_data[current_group][key] = value
    
    # Determine output path if not provided
    if output_path is None:
        notebook_path = Path(nb_path)
        output_path = notebook_path.with_suffix('.yaml')
    
    # Write to YAML file
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)
    
    print(f"YAML file saved to: {output_path}")

# %% ../nbs/nbs.ipynb 22
def export_ipynb_toml(
    nb_path: Optional[str] = None,
    output_path: Optional[str] = None
    ) -> None:
    """
    Export the content of the current Jupyter notebook to a TOML file.
    
    This function reads the content of the notebook where it's being executed,
    extracts all level 2 (##) markdown cells as groups, and all parameter assignments
    in code cells as key-value pairs within those groups. Regular text markdown cells are ignored.
    
    Parameters:
    -----------
    nb_path : str, optional
        Path to the notebook file. If None, the function will try to determin the
        current notebook path automatically (works in standard Jupyter but may not
        work in all environments like VS Code).
    output_path : str, optional
        Path where the TOML file should be saved. If None, the TOML file will be
        saved in the same directory as the notebook with the same name but with
        a .toml extension.
    
    Returns:
    --------
    None
    """
    # Get the path of the notebook that's currently being executed if not provided
    if nb_path is None:
        try:
            import IPython
            ipython = IPython.get_ipython()
            # Try different methods to get the notebook path
            if hasattr(ipython, 'kernel') and hasattr(ipython.kernel, 'path'):
                nb_path = ipython.kernel.path
            elif hasattr(ipython, 'ev'):
                # Try to get the path from the %notebook magic command history
                for line in ipython.history_manager.get_tail(100, include_latest=True):
                    if '%notebook' in line[2]:
                        parts = line[2].split()
                        for i, part in enumerate(parts):
                            if part == '%notebook' and i+1 < len(parts):
                                nb_path = parts[i+1]
                                break
        except (ImportError, AttributeError):
            pass
        
        if nb_path is None:
            raise ValueError(
                "Could not determine the notebook path automatically. "
                "Please provide the notebook_path parameter explicitly."
            )
    
    # Read the notebook
    with open(nb_path, 'r', encoding='utf-8') as f:
        notebook = nbformat.read(f, as_version=4)
    
    # Initialize variables
    toml_data = {}
    current_group = None
    
    # Process cells
    for cell in notebook.cells:
        # Process markdown cells to find level 2 headings
        if cell.cell_type == 'markdown':
            lines = cell.source.split('\n')
            for line in lines:
                if line.startswith('## '):
                    # Found a level 2 heading, use it as a group
                    current_group = line[3:].strip()
                    toml_data[current_group] = {}
        
        # Process code cells if we have a current group
        elif cell.cell_type == 'code' and current_group is not None:
            # Process each line in the code cell looking for parameter assignments
            code_lines = cell.source.split('\n')
            for line in code_lines:
                # Skip empty lines and comments
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Look for parameter assignments (var = value)
                if '=' in line:
                    # Skip lines that call export functions
                    if 'export_ipynb_' in line:
                        continue
                        
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value_str = parts[1].strip()
                        
                        # Try to evaluate the value to get proper types
                        try:
                            # Handle string values that might be quoted
                            if (value_str.startswith('"') and value_str.endswith('"')) or \
                               (value_str.startswith("'") and value_str.endswith("'")):
                                value = value_str[1:-1]  # Remove quotes
                            else:
                                # Try to evaluate as Python literal
                                import ast
                                value = ast.literal_eval(value_str)
                        except (SyntaxError, ValueError):
                            # If evaluation fails, use the string as is
                            value = value_str
                        
                        # Add to TOML data
                        toml_data[current_group][key] = value
    
    # Determine output path if not provided
    if output_path is None:
        notebook_path = Path(nb_path)
        output_path = notebook_path.with_suffix('.toml')

    # Write the TOML file manually to ensure proper formatting
    with open(output_path, 'w', encoding='utf-8') as f:
        for section, values in toml_data.items():
            f.write(f"[{section}]\n")
            for key, value in values.items():
                # For headers_to_split_on, we need to preserve the tuple structure
                if key == "headers_to_split_on" and isinstance(value, list) and all(isinstance(item, tuple) for item in value):
                    # Write as a TOML array of arrays
                    f.write(f"{key} = [\n")
                    for tup in value:
                        # Each tuple becomes an array in TOML
                        elements = []
                        for elem in tup:
                            if isinstance(elem, str):
                                elements.append(f'"{elem}"')
                            else:
                                elements.append(str(elem))
                        f.write(f"  [{', '.join(elements)}],\n")
                    f.write("]\n")
                else:
                    # For other values, use the standard TOML serialization
                    # Convert Python value to TOML-compatible string
                    if isinstance(value, str):
                        f.write(f'{key} = "{value}"\n')
                    elif isinstance(value, list):
                        # Format list elements properly
                        formatted_list = []
                        for item in value:
                            if isinstance(item, str):
                                formatted_list.append(f'"{item}"')
                            else:
                                formatted_list.append(str(item))
                        f.write(f"{key} = [{', '.join(formatted_list)}]\n")
                    else:
                        f.write(f"{key} = {value}\n")
            f.write("\n")

    print(f"TOML file saved to: {output_path}")
