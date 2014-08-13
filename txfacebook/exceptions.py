class GraphAPIError(Exception):
    def __init__(self, data):
        self.data = data
        self.type = self._get_type(data)
        self.message = self._get_message(data)
        super(Exception, self).__init__(self.message)

    @staticmethod
    def _get_type(response):
        try:
            return response['error_code']
        except KeyError:
            return None

    @staticmethod
    def _get_message(data):
        # OAuth 2.0 Draft 10
        try:
            return data['error_description']
        except KeyError:
            pass
        # OAuth 2.0 Draft 00
        try:
            return data['error']['message']
        except KeyError:
            pass

        # REST server style
        try:
            return data['error_msg']
        except KeyError:
            return str(data)
