from setuptools import setup, find_packages

setup(
    name="spopy-control",
    version="1.0.0",
    description='Controle de música do Spotify com gestos e voz',
    author='Seu Nome',
    author_email='seu.email@email.com',
    url='https://github.com/seu-usuario/skipspot',
    packages=find_packages(),
    install_requires=[
        'opencv-python',
        'numpy',
        'spotipy',
        'mediapipe',
        'pandas',
        'speech_recognition',
        'pyaudio'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
        'Operating System :: Microsoft :: Windows',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Scientific/Engineering :: Image Recognition'
    ],
    entry_points={
        'console_scripts': [
            'spopy-control=spopy_control:main'
        ]
    }
)
