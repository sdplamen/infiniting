# Empowering Photographers: A Django Social Media Platform

---

## Project Vision

As a dedicated hobby photographer and someone deeply dedicated to **B & W** and **Magnum Photography**, I recognize the unique needs of the photography community.
This **final project** for IT Step Academy's Computer Graphics and Design program is a social media platform crafted for photographers, emphasizing **Magnum Photography**.
It integrates **brand design identity** principles to create an engaging, community-driven experience for showcasing, sharing, and connecting through photography.

---

## UX/UI Design
Considering my graphic design expertise, I created a comprehensive __[UX/UI prototype in Figma](https://www.behance.net/gallery/153390325/UX-UI-project)__.
The design prioritizes intuitive navigation, visually appealing layouts, and a cohesive brand identity. Key features include streamlined photo uploads, portfolio galleries, and community interaction interfaces.

---

## Technical Foundation

Built with the **Django framework**, this platform reflects my 2+ years of Software Engineering with Python studies at SoftUni, Bulgaria. Key technical components include:
* **Models**: Custom database models for user profiles, photos, and comments to support community interactions.
* **Views & Templates**: Dynamic views and responsive templates for seamless gallery and feed rendering.
* **Authentication**: Secure user authentication and authorization using Django’s built-in system.
* **REST API**: Enables future integration with mobile apps or third-party services.
* **UNIT and INTEGRATION TESTS**: Comprehensive unit tests cover article approval and auction payment functionality, while integration tests ensure seamless new photo uploads.
---

## Presentation

Prepared for evaluation by SoftUni examiners, this project demonstrates my ability to blend graphic design with Python-based web development to create a meaningful platform for photographers.

-- 

### Considering this well-structured and quite comprehensive REST API built with Django Rest Framework.

Here's a breakdown of what's there :

* User Authentication :
    * The API has endpoints for user registration (/register/), login (/login/), and logout (/logout/).
    * It uses JSON Web Tokens (JWT) for authentication, which is a standard and secure method for APIs.

* API Endpoints for Your Core Features :
    * The API exposes CRUD (Create, Read, Update, Delete) operations for almost all of your application's models:
        * Photos: Can list, create, view, update, and delete photos.
        * Articles: Can manage articles.
        * Auctions and Bids: Can manage auctions and place bids.
        * Groups: Can manage groups and group memberships.
        * Interactions: Can manage likes, comments, and ratings.

* Data Serialization :
    * The serializers.py file defines how your Django models are converted to and from JSON. This is how the data is structured when it's sent over the network.

* Permissions :
    * The API has custom permission classes to control who can access which endpoints. For example, some endpoints are read-only for anonymous users, while others require the user to be authenticated or to be the owner of the resource.

What This Means :

* There is a powerful and fully functional REST API at your disposal. It's not just a "mobile API"; it's a complete backend API that can be used for any of the purposes we discussed earlier:

  * Ready to build a mobile app. There are all the necessary endpoints to build a full-featured iOS or Android application.
  * Start building a Single-Page Application (SPA) right away. Using a framework like React or Vue to build a modern frontend that communicates with this API.
  * Expose this as a public API. With some documentation, that could allow other developers to build applications on top of your platform.

###  Next Steps :

  * To build a mobile app? We can start by thinking about the features of the app and how they would map to the existing API endpoints.
  * To create a new frontend for your web app? Setting up a project with a modern JavaScript framework and how to connect it to your API.
  * To improve the existing API? Looking for areas to improve, for example, by adding more advanced features like filtering, searching, or pagination to your API endpoints.
