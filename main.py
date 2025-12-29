from fastapi import FastAPI
from typing import Optional
from pydantic import BaseModel

app = FastAPI()

@app.get("/")
def read_root():
    return {"Messeage": "Hello world"}

@app.get("/greet")
def greet():
    return {"Messeage": "Hello Sam"}

@app.get("/greet/")
def greet_name(name: str, age: Optional[int] = None):
    return {"Messeage": f"Hello {name} and you are {age} years old"}


class Student(BaseModel):
    name: str
    age: int
    roll: int

@app.post("/create_student")
def create_student(student: Student):
    return {
        "name": student.name,
        "age": student.age,
        "roll": student.roll
    }
