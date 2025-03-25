import sys

def check_import(package_name):
    try:
        __import__(package_name)
        print(f"✅ {package_name} is installed.")
    except ImportError:
        print(f"❌ {package_name} is NOT installed. Run: pip install {package_name}")

# Check required packages
required_packages = ["torch", "transformers", "sentencepiece"]

print("\n🔍 Checking required Python packages...\n")
for package in required_packages:
    check_import(package)

# Check PyTorch version and CUDA availability
try:
    import torch
    print(f"\n🔍 PyTorch Version: {torch.__version__}")
    if torch.cuda.is_available():
        print(f"✅ CUDA is available! GPU: {torch.cuda.get_device_name(0)}")
    else:
        print("⚠️ CUDA is NOT available. Running on CPU.")
except ImportError:
    print("\n❌ PyTorch is NOT installed. Run: pip install torch")

# Check Transformers version
try:
    import transformers
    print(f"\n🔍 Transformers Version: {transformers.__version__}")
except ImportError:
    print("\n❌ Transformers is NOT installed. Run: pip install transformers")

print("\n✅ Done! If there are any ❌ errors above, install the missing packages.")


import torch
print(torch.cuda.is_available())  # Should return True
print(torch.cuda.device_count())  # Should return the number of GPUs
print(torch.cuda.get_device_name(0))  # Should return RTX 3060

