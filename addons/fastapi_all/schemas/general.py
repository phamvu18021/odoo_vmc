from pydantic import BaseModel, field_validator
from typing import List, Optional


class WordPressInfo(BaseModel):
    idWordPress: str
    idOdoo: str
    slug: str
    categories: Optional[str] = None


class SchoolArea(BaseModel):
    name: str
    code: str


class Owner(BaseModel):
    name: str
    code: str


class Area(BaseModel):
    name: str
    code: str


class TeachField(BaseModel):
    name: str
    code: str


class Method(BaseModel):
    name: str
    code: str


class TrainingChannel(BaseModel):
    name: str
    code: str


class TotalTime(BaseModel):
    name: str
    code: str


class TotalTime(BaseModel):
    name: str
    code: str


class ExamLocation(BaseModel):
    name: str
    code: str


class Point(BaseModel):
    name: str
    code: str


class Place(BaseModel):
    name: str
    code: str


class Station(BaseModel):
    name: str
    title: str
    code: str


class Objects(BaseModel):
    name: str
    code: str


class TrainingTime(BaseModel):
    name: str
    code: str


class Type(BaseModel):
    name: str
    code: str


class BlockCombine(BaseModel):
    name: str
    code: str


class MajorCombine(BaseModel):
    name: str
    code: str


class School(BaseModel):
    name: str
    code: str
    image_course_thumb: Optional[str] = None
    img_url: Optional[str] = None

    @field_validator("image_course_thumb", "img_url", mode="before")
    def convert_false_to_none(cls, value):
        return value if value is not False else None


class Major(BaseModel):
    name: str
    code: str
    slug: Optional[str] = None
    image: Optional[str] = None
    block_combine: List[BlockCombine] = []
    major_combine: List[MajorCombine] = []

    @field_validator("slug", "image", mode="before")
    def convert_false_to_none(cls, value):
        return value if value is not False else None
