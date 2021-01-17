module IceGauntlet {

  exception Unauthorized {};

  interface Authentication {
    void changePassword(string user, string currentPassHash, string newPassHash) throws Unauthorized;
    string getNewToken(string user, string passwordHash) throws Unauthorized;
    bool isValid(string token);
    string getOwner(string token) throws Unauthorized;
  };

};
