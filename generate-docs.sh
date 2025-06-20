#/bin/bash

# Directory paths
ONTOLOGY_DIR="ontology"
DOCS_DIR="docs"
DIAGRAMS_DIR="diagrams"
EVAL_DIR="evaluation"

# STEP 1: ONTOLOGY CONCEPTUALIZATION

# Loop through each .drawio file in the diagrams directory
for directory in "$DIAGRAMS_DIR"/*/; do
    # Extract the module ename (without path or extension)
    module_name="$(basename "$directory")"
    # Export drawio diagrams PNG format
    docker run --rm -v $(pwd)/diagrams/"$module_name":/tmp/$module_name rlespinasse/drawio-export:v4.34.0 \
        --format png --output /tmp/"$module_name" --border 10 /tmp/$module_name/$module_name.drawio
    mv diagrams/$module_name/$module_name-$module_name.png diagrams/$module_name/$module_name.png
    # Export drawio diagrams SVG format
    docker run --rm -v $(pwd)/diagrams/"$module_name":/tmp/$module_name rlespinasse/drawio-export:v4.34.0 \
        --format svg --output /tmp/"$module_name" /tmp/$module_name/$module_name.drawio
    mv diagrams/$module_name/$module_name-$module_name.svg diagrams/$module_name/$module_name.svg
    # Export drawio diagrams XML format
    docker run --rm -v $(pwd)/diagrams/"$module_name":/tmp/$module_name rlespinasse/drawio-export:v4.34.0 \
        --format xml --output /tmp/"$module_name" /tmp/$module_name/$module_name.drawio
    mv diagrams/$module_name/$module_name-$module_name.xml diagrams/$module_name/$module_name.xml
done

# STEP 2: ONTOLOGY CODE GENERATED WITH CHOWLK

# Loop through each .drawio file in the diagrams directory
for directory in "$DIAGRAMS_DIR"/*/; do
    # Extract the module ename (without path or extension)
    module_name="$(basename "$directory")"
    if [[ "$module_name" == "overview" ]]; then
        continue
    fi
    # Call the API and extract the Turtle data
    response=$(curl -s -F "data=@diagrams/$module_name/$module_name.xml" https://chowlk.linkeddata.es/api)
    # Extract the ttl_data field using jq (requires jq installed)
    ttl=$(echo "$response" | jq -r '.ttl_data')
    # Save to .ttl file
    echo "$ttl" > "$ONTOLOGY_DIR/$module_name.ttl"
done

# STEP 3: ONTOLOGY DOCUMENTATION GENERATED WITH WIDOCO

# Check if the docs directory exists, create if not
mkdir -p "$DOCS_DIR"

# Loop through each .ttl file in the ontology directory
for file in "$ONTOLOGY_DIR"/*.ttl; do
    # Check if the file exists (in case there are no .ttl files)
    if [ -f "$file" ]; then
        # Extract the module ename (without path or extension)
        module_name="$(basename "$file" .ttl)"
        # Generate WIDOCO documentation using Docker
        docker run -ti --rm \
          -v `pwd`/ontology:/usr/local/widoco/in \
          -v `pwd`/docs/$module_name:/usr/local/widoco/out \
          ghcr.io/dgarijo/widoco:v1.4.25 -ontFile in/$module_name.ttl \
          -outFolder out -webVowl -oops  -getOntologyMetadata \
          -excludeIntroduction -htaccess -licensius -noPlaceHolderText

        # Use Git to checkout abstract and description sections in the document
        #git checkout docs/$module_name/sections/description-en.html

        # Copy ontology diagram into resources module
        mkdir $DOCS_DIR/$module_name/resources/images
        cp diagrams/$module_name/$module_name.svg $DOCS_DIR/$module_name/resources/images/

        # Insert chowlk diagram into description
        html_file="docs/$module_name/sections/description-en.html"
        replacement="

        <br/><br/>
        <center>
            <img src=\"resources/images/${module_name}.svg\" alt=\"General overview of the ontology\" width=\"75%\"><br/><br/><figcaption><b>Figure 1.</b> - General overview of the ontology.</figcaption>
        </center>"
        echo -e "$replacement" >> "$html_file"

        # Rename index html file
        mv $DOCS_DIR/$module_name/index-en.html $DOCS_DIR/$module_name/index.html

        # Copy OOPS! report to evaluation folder
        mkdir -p $EVAL_DIR/$module_name
        cp -r $DOCS_DIR/$module_name/OOPSevaluation $EVAL_DIR/$module_name/OOPS

    fi

done
