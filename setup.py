from setuptools import setup, find_packages

setup(
    name="supportai-chatbot",
    version="1.0.0",
    description="AI/ML-powered customer service chatbot using TF-IDF, SVM, and VADER sentiment analysis",
    author="Himanshu",
    python_requires=">=3.9",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "flask>=3.0.0",
        "scikit-learn>=1.3.0",
        "numpy>=1.24.0",
        "joblib>=1.3.0",
        "vaderSentiment>=3.3.2",
    ],
    entry_points={
        "console_scripts": [
            "supportai-train=train:train",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: Flask",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
)
