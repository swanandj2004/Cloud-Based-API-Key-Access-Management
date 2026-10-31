---- Cloud Based API Key Management Platform ----

API key management refers to generating, securely storing and controlling user access to the API keys. 
There are two types of roles - admin and user. An admin has a high set of permissions while a user has limited set of permissions.
This implementation covers the following :
  - Creating and managing roles
  - User sign up and user login
  - Updating user details
  - Resetting password securely, if user forgets it
  - Generating API keys
  - Controlling user access to API keys via user id
  - Storing user's password in hashed format for ensuring security
  - Storing API keys in an encrypted format, while they get decrypted when an authorized user tries to access them
  - json web token (jwt) is used for authentication and authorization of the API endpoints
  - jwt also provides role based access control and password reset
