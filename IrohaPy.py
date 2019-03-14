#!/usr/bin/env python
# coding: utf-8

# In[1]:


from iroha import Iroha, IrohaGrpc, IrohaCrypto
from iroha.primitive_pb2 import can_set_my_account_detail, can_receive, can_transfer

import binascii
from random import randint
from itertools import product

from guizero import App, Text, Window, PushButton, ButtonGroup, TextBox, ListBox


# # Network configuration

# In[2]:


domain_name = "animal"


# In[3]:


admin_private_key = 'f101537e319568c765b2cc89698325604991dca57b9716b58016b253506cab70'
iroha = Iroha('admin@test')
net = IrohaGrpc()


# # Some helpful methods

# In[4]:


def send_transaction_and_print_status(transaction):
    hex_hash = binascii.hexlify(IrohaCrypto.hash(transaction))
    print('Transaction hash = {}, creator = {}'.format(
        hex_hash, transaction.payload.reduced_payload.creator_account_id))
    net.send_tx(transaction)
    return list(net.tx_status_stream(transaction))


# In[5]:


def admin_details():
    query = iroha.query('GetAccountAssets', account_id=f'admin@test')
    IrohaCrypto.sign_query(query, admin_private_key)

    response = net.send_query(query)
    data = response.account_assets_response.account_assets
    for asset in data:
        print('Asset id = {}, balance = {}'.format(
            asset.asset_id, asset.balance))


# # Lets create some assets and add some quantity

# In[6]:


animals = [
    "cows",
    "pigs",
    "bull",
    "horse"
] # uses as assets


# In[7]:


commands = [
    iroha.command('CreateDomain', domain_id=domain_name, default_role='user'),
     *[iroha.command('CreateAsset', asset_name=animal,
                   domain_id=domain_name, precision=0)
          for animal in animals]
]
tx = IrohaCrypto.sign_transaction(
    iroha.transaction(commands), admin_private_key)
send_transaction_and_print_status(tx)


# In[8]:


admin_details()


# In[9]:


tx = iroha.transaction([
    iroha.command('AddAssetQuantity',
                  asset_id=f'{animal}#{domain_name}', amount='100')
      for animal in animals
])
IrohaCrypto.sign_transaction(tx, admin_private_key)
send_transaction_and_print_status(tx)


# In[10]:


admin_details()


# # Lets create main class for ledger - Farm class

# In[11]:


class Farm:    
    def __init__(self, account_name, domain):
        self.account_name = account_name
        self.domain = domain
        self.full_name = f"{self.account_name}@{self.domain}"
        self.__private_key = IrohaCrypto.private_key()
        self.public_key = IrohaCrypto.derive_public_key(self.__private_key)
        self.iroha = Iroha(self.full_name)
    
    def get_cattle(self):
        query = self.iroha.query('GetAccountAssets', account_id=self.full_name)
        IrohaCrypto.sign_query(query, self.__private_key)

        response = net.send_query(query)
        data = response.account_assets_response.account_assets
        return {asset.asset_id.split('#')[0]: asset.balance for asset in data}
        
        
    def transfer_animal(self, name_to, animal, amount):
        reciever = f"{name_to}@{self.domain}"
        tx = self.iroha.transaction(
            [
                iroha.command(
                    "TransferAsset",
                    src_account_id=self.full_name,
                    dest_account_id=reciever,
                    asset_id=f"{animal}#{self.domain}",
                    description="transfer",
                    amount=str(amount),
                )
            ]
        )
        IrohaCrypto.sign_transaction(tx, self.__private_key)
        return send_transaction_and_print_status(tx)


# In[12]:


farm_names = ["miratorg", "happy", "greatest", "milk"]


# In[13]:


farms = [Farm(name, domain_name) for name in farm_names]


# In[14]:


tx = iroha.transaction([
    iroha.command('CreateAccount', account_name=farm.account_name, domain_id=farm.domain,
                  public_key=farm.public_key)
    for farm in farms
])
IrohaCrypto.sign_transaction(tx, admin_private_key)
send_transaction_and_print_status(tx)


# ## Lets add some random initial asset to all farms

# In[15]:


tx = iroha.transaction([
    iroha.command('TransferAsset', src_account_id='admin@test', dest_account_id=f'{name}@{domain_name}',
                  asset_id=f'{asset}#{domain_name}', amount=str(randint(1, 10)))
    for asset, name in product(animals, farm_names)
])
IrohaCrypto.sign_transaction(tx, admin_private_key)
send_transaction_and_print_status(tx)


# In[16]:


admin_details()


# ## Lets test transfering between accounts

# In[17]:


farms[0].get_cattle()['horse']


# In[18]:


farms[1].get_cattle()['horse']


# In[19]:


farms[0].transfer_animal(farms[1].account_name, 'horse', 8)


# In[20]:


farms[0].get_cattle()['horse']


# In[21]:


farms[1].get_cattle()['horse']


# ### As we can see, number of cows in first firm decreased and in second increased.
# ### So, system works
# ### Lets have more fun with GUI

# # GUI PART

# In[22]:


def get_info_for_farm(farm):
    stats = str(farm.get_cattle()).strip('{}').strip("''")
    message = f"""On farm {farm.account_name} left:\n{stats}"""
    return message


# In[23]:


def update_info_for_farm(text, farm):  
    message = get_info_for_farm(farm)
    text.value = message


# In[24]:


def update_info_for_all_farms(text):
    message = '\n\n'.join([get_info_for_farm(farm) for farm in farms])
    text.value = message


# In[25]:


def transfer(farm, whom, what, how_many, status, history):
    whom, what, how_many = whom.get(), what.get(), how_many.get()
    print(f"request to send from {farm.account_name} to {whom} {what} in amount {how_many}")
    result = farm.transfer_animal(whom, what, int(how_many))
    result = '\n'.join([str(r) for r in result]) 
    print(result)
    history.append(result)
    status.value = f"Status:\n{result}"


# In[26]:


def create_app():
    app = App(title="Main window for admin")
    status_for_all = Text(app, text="")
    status_for_all.repeat(1000, update_info_for_all_farms, [status_for_all])
    
    operation_history_text = Text(app, text="\n\nTransaction history:")
    history = ListBox(app, scrollbar=True)
    
    for i, farm in enumerate(farms):
        window = Window(app, title=f"Window for {farm.account_name}")
        text = Text(window, text="")
        text.repeat(1000, update_info_for_farm, [text, farm])
        bg = ButtonGroup(window, options=animals)
        text = Text(window, text="Send to:")
        whom = TextBox(window, text='')
        text = Text(window, text="Amount:")
        how_many = TextBox(window)
        status = Text(window, text="Status:")
        button = PushButton(window, transfer, text="Transfer!", 
                            args=[farm, whom, bg, how_many, status, history])
        
    app.display()


# In[ ]:


create_app()


# In[ ]:




