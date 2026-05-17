"""Setup script for Music Video Compiler."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="music-video-compiler",
    version="1.0.0",
    author="Music Video Compiler Team",
    description="Professional Music Compilation Video Creator",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Satrioadi017/music-video-compiler",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "PyQt5>=5.15.0",
        "Pillow>=9.0.0",
    ],
    entry_points={
        "console_scripts": [
            "music-video-compiler=music_video_compiler.gui:run_app",
        ],
        "gui_scripts": [
            "mvc-gui=music_video_compiler.gui:run_app",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Video",
        "Topic :: Multimedia :: Sound/Audio",
    ],
)
