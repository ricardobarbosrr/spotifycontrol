from setuptools import setup

setup(
    name='skipspot',
    version='1.0.0',
    description='Controle de música do Spotify com gestos e voz',
    author='Seu Nome',
    author_email='seu.email@email.com',
    url='https://github.com/seu-usuario/skipspot',
    packages=['skipspot'],
    install_requires=[
        'opencv-python==4.8.0.74',
        'numpy==1.24.3',
        'spotipy==2.23.0',
        'mediapipe==0.10.11',
        'pandas==2.0.3',
        'speech_recognition==3.14.2',
        'pyaudio==0.2.14'
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
            'skipspot=skipspot:main'
        ]
    }
)
