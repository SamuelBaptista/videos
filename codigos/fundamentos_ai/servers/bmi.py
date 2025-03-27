from mcp.server.fastmcp import FastMCP

mcp = FastMCP("My App")

@mcp.tool()
def calculate_bmi(weight_kg: float, height_m: float) -> float:
    """Calculate BMI given weight in kg and height in meters"""
    return weight_kg / (height_m**2)

# [protocol]://[host]/[path]
@mcp.resource("json://profile/{user_name}")
def get_user_profile(user_name: str) -> str:
    """Return the weight_kg and height_m of a user"""

    database = {
        "samuel": {"weight_kg": 95, "height_m": 1.77},
        "maria": {"weight_kg": 60, "height_m": 1.65},
    }

    return database[user_name]

@mcp.prompt()
def check_bmi(bmi: float, user_name: str) -> str:
    """Check the BMI based on user's name"""

    prompts = {
        "samuel": f"Eu sou um atleta, considere isso e faça uma avaliação do meu BMI:\n\n{bmi}",
        "maria": f"Eu sou uma senhora de 70 anos, considere isso e faça uma avaliação do meu BMI:\n\n{bmi}"
    }

    return prompts[user_name]


if __name__ == "__main__":
    mcp.run()