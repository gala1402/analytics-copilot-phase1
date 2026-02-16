def compose(user_input, tasks, results):

    output = "### Original Request\n" + user_input + "\n\n"

    for task in tasks:
        if task["supported"]:
            result = next((r for r in results if r["id"] == task["id"]), None)
            output += f"### {task['intent']}\n"
            output += result["output"] + "\n\n"
        else:
            output += f"### Unsupported Task\n"
            output += f"{task['question']}\n"
            output += "This falls outside analytics scope. I can instead provide a metrics plan or executive summary.\n\n"

    return output
