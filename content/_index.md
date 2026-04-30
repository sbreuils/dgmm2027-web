---
# Leave the homepage title empty to use the site title
title: ''
date: 2022-10-24
type: landing

design:
  # Default section spacing
  spacing: '6rem'
sections:
  - block: hero
    content:
      title: ""
      text: |
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 40px; align-items: center; position: relative; z-index: 2;">
          
          <div style="text-align: left;">
            <h1 style="color: #000000; font-size: 3.5rem; font-weight: 800; line-height: 1.1; margin-bottom: 20px;">
              GT GDMM
            </h1>
            
            <div style="color: #333333; font-size: 1.3rem; font-weight: 500; line-height: 1.6;">
              <p style="margin-bottom: 10px;">
                Groupe de Travail <b>Géométrie Discrète</b> et <b>Morphologie Mathématique</b>.
              </p>
              <p style="font-size: 1.1rem; color: #555;">
                Bienvenue sur le site du GT commun aux GdR IM et IG-RV.
              </p>
            </div>
            
            <br>
            <a href="#news" class="btn btn-primary btn-lg" style="border-radius: 5px;">Voir les actualités</a>
          </div>

          <div style="text-align: center;">
             <img src="/media/gdr.png" alt="Logos Partenaires" style="max-width: 350px; width: 100%; height: auto;">
          </div>
          
        </div>

    design:
      # "2" divise l'écran : Texte à gauche | Image (gdr.png) à droite
      columns: '1'
      
      background:
        # C'est ce paramètre qui place l'image en FOND (derrière le texte)
        image:
          filename: "logo_gdmm.png"
          size: "contain" 
          position: "center right"
          
        css_style: |
          background-image: url('/media/logo_gdmm.png');
          background-size: 500px; /* On force une taille RAISONNABLE */
          background-repeat: no-repeat;
          background-position: right center; /* On la cale à droite */
          background-blend-mode: overlay; /* Elle se fond dans le gris */
          opacity: 1;
        
      # Ajustement de la taille de l'image de droite (GDMM)
      css_class: "hero-text-align-left"
  - block: collection
    id: news
    content:
      title: Dernières Annonces
      page_type: post
      count: 5
      filters:
        exclude_future: true
        order: desc
    design:
      view: compact
---
