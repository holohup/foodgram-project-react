#!/bin/bash
echo "Starting process."
echo "Preloading fixtures."
python manage.py loaddata fixtures/presets.json
echo "Copying images."
if [ -d "media/recipes" ] 
then
    echo "Recipes directory found, copying images"
else
    echo "Recipes images directory not found, creating it." 
    mkdir media/recipes
fi
cp fixtures/images/* media/recipes/
echo "Presets loading complete."
