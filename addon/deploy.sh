clasp push
clasp deploy --description "Gmail Add-on $(date +%Y%m%d-%H%M%S)"
echo "Deployment complete! Now:"
echo "1. Go to https://script.google.com"
echo "2. Open your project"
echo "3. Click Deploy > Test deployments"
echo "4. Click Install"
echo "5. Refresh Gmail and open an email"
echo "6. Look for the add-on icon on the right sidebar"