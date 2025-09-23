# Pandoc/Extra Deployment Guide

This guide provides comprehensive instructions for deploying and using the `pandoc/extra:3.7` Docker image using both Docker CLI and Minikube.

## Prerequisites

Before starting, ensure you have the following installed:

- **Docker**: For containerized pandoc functionality
- **Minikube**: For Kubernetes deployment testing
- **kubectl**: Kubernetes command-line tool
- **Python 3.12+**: For running the demo notebook

## Docker CLI Deployment

### 1. Pull the pandoc/extra:3.7 Image

#### For x86_64 Systems (Intel/AMD)
```bash
docker pull pandoc/extra:3.7
```

#### For ARM64 Systems (Apple Silicon, Windows ARM64)
The pandoc/extra:3.7 image is only available for x86_64 architecture. On ARM64 systems, you must use platform emulation:

```bash
# Pull with platform emulation for ARM64 systems
docker pull --platform linux/amd64 pandoc/extra:3.7
```

**Note**: If you get an error like "no matching manifest for linux/arm64", this confirms you need the emulated x86_64 version.

### 2. Verify Installation

#### For x86_64 Systems
```bash
# Check if image is available locally
docker images pandoc/extra:3.7

# Test pandoc functionality
docker run --rm pandoc/extra:3.7 --version
```

#### For ARM64 Systems (with emulation)
```bash
# Check if image is available locally
docker images pandoc/extra:3.7

# Test pandoc functionality with platform emulation
docker run --platform linux/amd64 --rm pandoc/extra:3.7 --version
```

### 3. Basic Usage Examples

#### Convert LaTeX to PDF

**For x86_64 Systems:**
```bash
# Mount current directory and convert file
docker run --rm -v $(pwd):/data pandoc/extra:3.7 test/data/basic_example.tex -o /data/output.pdf --pdf-engine=pdflatex
```

**For ARM64 Systems (with emulation):**
```bash
# Mount current directory and convert file with platform emulation
docker run --platform linux/amd64 --rm -v $(pwd):/data pandoc/extra:3.7 test/data/basic_example.tex -o /data/output.pdf --pdf-engine=pdflatex
```

#### Convert LaTeX to HTML

**For x86_64 Systems:**
```bash
docker run --rm -v $(pwd):/data pandoc/extra:3.7 test/data/basic_example.tex -o /data/output.html --standalone --mathjax
```

**For ARM64 Systems (with emulation):**
```bash
docker run --platform linux/amd64 --rm -v $(pwd):/data pandoc/extra:3.7 test/data/basic_example.tex -o /data/output.html --standalone --mathjax
```

#### Convert LaTeX to Markdown

**For x86_64 Systems:**
```bash
docker run --rm -v $(pwd):/data pandoc/extra:3.7 test/data/basic_example.tex -o /data/output.md --from=latex --to=markdown
```

**For ARM64 Systems (with emulation):**
```bash
docker run --platform linux/amd64 --rm -v $(pwd):/data pandoc/extra:3.7 test/data/basic_example.tex -o /data/output.md --from=latex --to=markdown
```

#### Convert LaTeX to DOCX

**For x86_64 Systems:**
```bash
docker run --rm -v $(pwd):/data pandoc/extra:3.7 test/data/basic_example.tex -o /data/output.docx
```

**For ARM64 Systems (with emulation):**
```bash
docker run --platform linux/amd64 --rm -v $(pwd):/data pandoc/extra:3.7 test/data/basic_example.tex -o /data/output.docx
```

### 4. Advanced Docker Usage

#### With Custom Working Directory
```bash
docker run --rm -v /path/to/your/files:/workdir pandoc/extra:3.7 /workdir/input.tex -o /workdir/output.pdf --pdf-engine=pdflatex
```

#### With Environment Variables
```bash
docker run --rm -e PANDOC_VERSION=3.7 -v $(pwd):/data pandoc/extra:3.7 test/data/basic_example.tex -o /data/output.pdf
```

## Minikube Deployment

### 1. Start Minikube

```bash
# Start minikube cluster
minikube start

# Verify status
minikube status
```

### 2. Create Kubernetes Deployment

Create a file named `k8s-pandoc-deployment.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pandoc-extra-pod
  labels:
    app: pandoc-extra
spec:
  containers:
  - name: pandoc-container
    image: pandoc/extra:3.7
    command: ["sleep", "infinity"]  # Keep container running
    volumeMounts:
    - name: shared-data
      mountPath: /data
    resources:
      requests:
        memory: "256Mi"
        cpu: "250m"
      limits:
        memory: "512Mi"
        cpu: "500m"
  volumes:
  - name: shared-data
    emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: pandoc-service
spec:
  selector:
    app: pandoc-extra
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
  type: ClusterIP
```

### 3. Deploy to Minikube

```bash
# Apply the configuration
kubectl apply -f k8s-pandoc-deployment.yaml

# Check pod status
kubectl get pods -l app=pandoc-extra

# Check service status
kubectl get services pandoc-service
```

### 4. Test Pandoc in Kubernetes

```bash
# Test pandoc version
kubectl exec pandoc-extra-pod -- pandoc --version

# Copy file to pod and convert
kubectl cp input.tex pandoc-extra-pod:/data/input.tex
kubectl exec pandoc-extra-pod -- pandoc /data/input.tex -o /data/output.pdf --pdf-engine=pdflatex
kubectl cp pandoc-extra-pod:/data/output.pdf ./output.pdf
```

### 5. Advanced Kubernetes Usage

#### With Persistent Volume
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pandoc-storage
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

#### With ConfigMap for Input Files
```bash
# Create configmap from files
kubectl create configmap pandoc-inputs --from-file=./input-files/

# Mount in deployment
volumeMounts:
- name: input-files
  mountPath: /inputs
volumes:
- name: input-files
  configMap:
    name: pandoc-inputs
```

### 6. Cleanup

```bash
# Delete the deployment
kubectl delete -f k8s-pandoc-deployment.yaml

# Stop minikube (optional)
minikube stop
```

## Sidecar Architecture Integration

### FastAPI Integration

The pandoc/extra container can be used as a sidecar alongside a FastAPI application:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pandoc-sidecar-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: pandoc-sidecar
  template:
    metadata:
      labels:
        app: pandoc-sidecar
    spec:
      containers:
      - name: fastapi-app
        image: your-fastapi-app:latest
        ports:
        - containerPort: 8000
        volumeMounts:
        - name: shared-data
          mountPath: /app/data
      - name: pandoc-container
        image: pandoc/extra:3.7
        command: ["sleep", "infinity"]
        volumeMounts:
        - name: shared-data
          mountPath: /data
      volumes:
      - name: shared-data
        emptyDir: {}
```

### Communication Between Containers

The FastAPI application can execute pandoc commands using subprocess:

```python
import subprocess

def convert_latex_to_pdf(input_file, output_file):
    cmd = ['pandoc', input_file, '-o', output_file, '--pdf-engine=pdflatex']
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0
```

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure Docker has proper permissions to mount volumes
2. **Pod Not Starting**: Check resource limits and image availability
3. **Pandoc Errors**: Verify input file format and pandoc arguments
4. **ARM64 Platform Issues**:
   - If you get "no matching manifest for linux/arm64", use `--platform linux/amd64`
   - Emulation performance may be 2-5x slower than native x86_64
   - Increase timeout values for complex document conversions on ARM64 systems

### Debugging Commands

```bash
# Check Docker logs
docker logs <container_id>

# Check Kubernetes pod logs
kubectl logs pandoc-extra-pod

# Describe pod for detailed status
kubectl describe pod pandoc-extra-pod

# Check available images in Minikube
minikube ssh docker images
```

### Performance Optimization

1. **Resource Limits**: Adjust CPU and memory based on document complexity
2. **Volume Types**: Use persistent volumes for large datasets
3. **Image Caching**: Pre-pull images on nodes for faster startup

## Security Considerations

1. **Volume Mounts**: Limit mounted directories to necessary paths only
2. **Resource Limits**: Set appropriate CPU and memory limits
3. **Network Policies**: Restrict pod-to-pod communication if needed
4. **Image Security**: Regularly update to latest pandoc/extra versions

## Version Information

- **pandoc/extra**: 3.7
- **Tested with**: Minikube v1.32+, Docker 20.10+
- **Kubernetes**: v1.28+

For more information, refer to the [official Pandoc documentation](https://pandoc.org/) and [pandoc/extra Docker Hub page](https://hub.docker.com/r/pandoc/extra).