from setuptools import setup, find_packages

setup(
    name='ragdotpy',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'google-generativeai',
        'chromadb',
        'pypdf2',
        'python-docx',
        'pandas',
        'beautifulsoup4',
        'rich',
        'python-dotenv',
        'tqdm'
    ],
    entry_points={
        'console_scripts': [
            'rag_sys = rag_sys.cli:main',
        ],
    },
)