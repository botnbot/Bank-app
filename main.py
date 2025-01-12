import re

from src.utils import filter_dataframe, get_data, greetings

pattern = re.compile(r"^\s*[A-ZА-ЯЁ]{1}[a-zа-яё]+\s+[A-ZА-ЯЁ]{1}\.\s*$")
df = get_data("data/operations.xlsx")
colname = {"Категория": "Переводы", "Описание": pattern}
print(filter_dataframe(df, colname, "AND"))
