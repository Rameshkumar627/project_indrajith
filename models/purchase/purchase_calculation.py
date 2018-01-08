
class PurchaseCalculation():

    def calculate_percentage(self, amount, percentage):
        value = 0
        if percentage:
            value = (float(amount) * float(percentage)) / 100

        return value

    def calculate_tax(self, amount, tax_value, tax_name):
        value = 0
       
        if tax_value != 0:
            value = self.calculate_percentage(amount, tax_value)

        if tax_name == 'IGST':
            IGST = value
            CGST = 0
            SGST = 0
        elif tax_name == 'GST':
            IGST = 0
            CGST = value / 2
            SGST = value / 2
        else:
            IGST = CGST = SGST = 0

        return IGST, CGST, SGST
        
       







